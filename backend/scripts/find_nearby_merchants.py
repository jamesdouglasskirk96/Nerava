#!/usr/bin/env python3
"""
Find Nearby Merchants Script - V2 (Fixed Corporate Detection)

Finds merchants within walking distance of EV chargers, within a driving radius of home.
Uses multi-layer corporate classification with decision friction scoring.

Output:
- outputs/merchants_closeable.csv - Top 100 truly closeable independents
- outputs/merchants_closeable.json - Same in JSON
- outputs/merchants_review.csv - Ambiguous/franchise candidates for manual review
- outputs/merchants_corporate.csv - Definite corporate (do not call)

Usage:
    python scripts/find_nearby_merchants.py

Environment Variables:
    GOOGLE_PLACES_API_KEY - Required for Google Places API
    NREL_API_KEY - Optional, for NREL Alternative Fuel Stations API
"""

import csv
import hashlib
import json
import math
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, urlparse

import requests

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class Config:
    """Configuration for the merchant finder."""
    home_address: str = "11621 Timber Heights Dr, Austin, TX"
    drive_time_minutes: int = 90
    walk_time_minutes: int = 5
    charger_search_radius_miles: int = 90
    merchant_search_radius_m: int = 500
    walk_speed_mps: float = 1.4

    merchant_types: list = field(default_factory=lambda: [
        "restaurant",
        "cafe",
        "bar",
        "bowling_alley",
        "movie_theater",
        "amusement_center",
        "gym",
        "bakery",
        "meal_takeaway",
        "night_club",
    ])

    brand_location_threshold: int = 3
    places_requests_per_second: float = 10.0
    nrel_requests_per_second: float = 5.0

    cache_dir: str = ".cache"
    output_dir: str = "outputs"
    denylist_path: str = "data/chain_denylist.txt"

    max_chargers: int = 200
    max_merchants_per_charger: int = 20
    top_n_merchants: int = 100

    # Enable/disable expensive validations
    validate_drive_time: bool = False  # Set True to use Distance Matrix API


# ============================================================================
# Utilities
# ============================================================================

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in meters."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def walk_time_minutes(distance_m: float, speed_mps: float = 1.4) -> float:
    return distance_m / speed_mps / 60


def get_cache_path(cache_dir: str, key: str, suffix: str = ".json") -> Path:
    hash_key = hashlib.md5(key.encode()).hexdigest()[:16]
    return Path(cache_dir) / f"{hash_key}{suffix}"


def load_from_cache(cache_path: Path) -> Optional[dict]:
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except:
            pass
    return None


def save_to_cache(cache_path: Path, data: dict):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(data, f)


class RateLimiter:
    def __init__(self, requests_per_second: float):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0

    def wait(self):
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()


def normalize_name(name: str) -> str:
    """Normalize business name for matching."""
    name = name.lower().strip()
    # Remove location suffixes
    name = re.sub(r'\s*[-–—]\s*[a-z\s]+(mall|center|plaza|square|village|commons|crossing).*$', '', name, flags=re.IGNORECASE)
    # Remove store numbers
    name = re.sub(r'\s*#\d+.*$', '', name)
    name = re.sub(r'\s+store\s*#?\d+.*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+location\s*#?\d+.*$', '', name, flags=re.IGNORECASE)
    # Remove "at [Location]"
    name = re.sub(r'\s+at\s+[a-z\s]+$', '', name, flags=re.IGNORECASE)
    # Remove common suffixes
    name = re.sub(r'\s+(inc|llc|corp|co|ltd)\.?$', '', name, flags=re.IGNORECASE)
    return name.strip()


def extract_brand_domain(website: str) -> Optional[str]:
    """Extract the brand domain from a website URL."""
    if not website:
        return None
    try:
        parsed = urlparse(website)
        domain = parsed.netloc.lower()
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        # Get main domain (remove subdomains for multi-location sites)
        parts = domain.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return domain
    except:
        return None


# ============================================================================
# Known Corporate Domains
# ============================================================================

CORPORATE_DOMAINS = {
    # Fast Food
    'mcdonalds.com', 'bk.com', 'wendys.com', 'tacobell.com', 'kfc.com',
    'chickfila.com', 'popeyes.com', 'arbys.com', 'sonicdrivein.com',
    'jackinthebox.com', 'whataburger.com', 'carlsjr.com', 'hardees.com',
    'fiveguys.com', 'in-n-out.com', 'culvers.com', 'raisingcanes.com',
    'wingstop.com', 'buffalowildwings.com', 'zaxbys.com', 'shakeshack.com',

    # Fast Casual
    'chipotle.com', 'panerabread.com', 'qdoba.com', 'moes.com',
    'pandaexpress.com', 'noodles.com', 'firehousesubs.com', 'jerseymikes.com',
    'jimmyjohns.com', 'subway.com', 'potbelly.com', 'mcalistersdeli.com',
    'jasonsdeli.com', 'tropicalsmoothie.com', 'smoothieking.com',
    'blazepizza.com', 'modpizza.com', 'cava.com', 'sweetgreen.com',
    'thekebabshop.com', 'ikesloveandsandwiches.com',

    # Coffee
    'starbucks.com', 'dunkindonuts.com', 'peets.com', 'dutchbros.com',
    'timhortons.com', 'cariboucoffee.com', 'coffeebean.com', 'philzcoffee.com',

    # Casual Dining
    'applebees.com', 'chilis.com', 'tgifridays.com', 'olivegarden.com',
    'redlobster.com', 'outback.com', 'texasroadhouse.com', 'longhornsteakhouse.com',
    'crackerbarrel.com', 'dennys.com', 'ihop.com', 'wafflehouse.com',
    'thecheesecakefactory.com', 'pfchangs.com', 'bjsrestaurants.com',
    'redrobin.com', 'bonefishgrill.com', 'carrabbas.com',

    # Asian
    'benihana.com', 'konagrill.com', 'genghisgrill.com', 'peiwei.com',

    # Ice Cream/Dessert
    'baskinrobbins.com', 'coldstonecreamery.com', 'dairyqueen.com',
    'jamba.com', 'insomnia.com', 'crumblcookies.com',

    # Salon/Beauty
    'ulta.com', 'sephora.com', 'greatclips.com', 'supercuts.com',
    'sportclips.com', 'massageenvy.com', 'europeanwax.com', 'drybar.com',

    # Fitness
    'planetfitness.com', 'lafitness.com', '24hourfitness.com', 'goldsgym.com',
    'anytimefitness.com', 'orangetheory.com', 'equinox.com', 'lifetime.life',

    # Hotels
    'marriott.com', 'hilton.com', 'hyatt.com', 'ihg.com', 'wyndhamhotels.com',
    'choicehotels.com', 'bestwestern.com', 'laquinta.com',

    # Gas/Convenience
    '7-eleven.com', 'circlek.com', 'quiktrip.com', 'wawa.com', 'sheetz.com',
    'bucees.com', 'loves.com', 'pilotflyingj.com',
}


# ============================================================================
# Corporate Classification - Multi-Layer
# ============================================================================

class CorporateClassifier:
    """Multi-layer corporate classification."""

    # Place types that indicate corporate/problematic locations
    CORPORATE_TYPES = {
        "department_store", "shopping_mall", "supermarket", "drugstore",
        "gas_station", "convenience_store", "bank", "atm", "car_dealer",
        "car_rental", "car_repair", "car_wash", "lodging", "hotel",
        "insurance_agency", "real_estate_agency",
    }

    # Types that indicate salon suite / micro-business (low value for cold calling)
    SALON_SUITE_TYPES = {"hair_salon", "beauty_salon", "nail_salon", "skin_care_clinic"}

    # Types that indicate inside a mall
    MALL_INDICATOR_TYPES = {"shopping_mall", "department_store"}

    def __init__(self, denylist_path: str):
        self.denylist_patterns = []
        self.denylist_regex = []
        self._load_denylist(denylist_path)

    def _load_denylist(self, path: str):
        if not os.path.exists(path):
            print(f"Warning: Denylist file not found at {path}")
            return

        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if line.startswith('regex:'):
                    pattern = line[6:].strip()
                    try:
                        self.denylist_regex.append(re.compile(pattern, re.IGNORECASE))
                    except re.error:
                        pass
                else:
                    self.denylist_patterns.append(line.lower())

        print(f"Loaded {len(self.denylist_patterns)} denylist patterns and {len(self.denylist_regex)} regex patterns")

    def classify(self, name: str, types: list, website: str, rating_count: int,
                 address: str) -> dict:
        """
        Multi-layer corporate classification.

        Returns dict with:
            - corporate_likely (bool)
            - corporate_reason (str)
            - needs_review (bool)
            - decision_friction (int 0-3)
            - friction_reason (str)
            - category (str: 'closeable', 'review', 'corporate')
        """
        result = {
            'corporate_likely': False,
            'corporate_reason': '',
            'needs_review': False,
            'decision_friction': 0,
            'friction_reason': 'independent',
            'category': 'closeable'
        }

        name_lower = name.lower()
        name_normalized = normalize_name(name)
        merchant_types = set(types) if types else set()

        # =====================================================================
        # LAYER A: Hard Denylist (exact/substring match on normalized name)
        # =====================================================================
        for pattern in self.denylist_patterns:
            if pattern in name_lower or pattern in name_normalized:
                result['corporate_likely'] = True
                result['corporate_reason'] = f"Denylist match: {pattern}"
                result['decision_friction'] = 3
                result['friction_reason'] = 'national_chain'
                result['category'] = 'corporate'
                return result

        # Check regex patterns
        for regex in self.denylist_regex:
            if regex.search(name) or regex.search(name_normalized):
                result['corporate_likely'] = True
                result['corporate_reason'] = f"Regex pattern match"
                result['decision_friction'] = 3
                result['friction_reason'] = 'franchise_naming'
                result['category'] = 'corporate'
                return result

        # =====================================================================
        # LAYER B: Website Domain Check
        # =====================================================================
        domain = extract_brand_domain(website)
        if domain and domain in CORPORATE_DOMAINS:
            result['corporate_likely'] = True
            result['corporate_reason'] = f"Corporate domain: {domain}"
            result['decision_friction'] = 3
            result['friction_reason'] = 'corporate_website'
            result['category'] = 'corporate'
            return result

        # =====================================================================
        # LAYER C: Place Type Checks
        # =====================================================================

        # Check for corporate place types
        corporate_type_matches = merchant_types & self.CORPORATE_TYPES
        if corporate_type_matches:
            result['corporate_likely'] = True
            result['corporate_reason'] = f"Corporate place type: {', '.join(corporate_type_matches)}"
            result['decision_friction'] = 3
            result['friction_reason'] = 'corporate_category'
            result['category'] = 'corporate'
            return result

        # Check for salon suite / micro-business
        if merchant_types & self.SALON_SUITE_TYPES:
            # Check if it's likely a salon suite (common indicators)
            salon_suite_indicators = [
                'salon loft', 'salon suite', 'phenix', 'sola salon',
                'my salon', 'salon plaza', 'the salon'
            ]
            if any(ind in name_lower for ind in salon_suite_indicators):
                result['needs_review'] = True
                result['decision_friction'] = 2
                result['friction_reason'] = 'salon_suite_micro'
                result['category'] = 'review'
                return result

        # =====================================================================
        # LAYER D: Location-Based Friction
        # =====================================================================
        address_lower = address.lower() if address else ''

        # Inside a hotel
        hotel_indicators = ['marriott', 'hilton', 'hyatt', 'holiday inn', 'hampton',
                          'courtyard', 'residence inn', 'fairfield', 'westin',
                          'sheraton', 'doubletree', 'embassy suites', 'hotel']
        if any(h in name_lower or h in address_lower for h in hotel_indicators):
            result['needs_review'] = True
            result['decision_friction'] = 2
            result['friction_reason'] = 'hotel_property'
            result['corporate_reason'] = 'Located in/at hotel'
            result['category'] = 'review'
            return result

        # Inside a mall
        mall_indicators = ['mall', 'galleria', 'shopping center', 'outlet',
                         'town center', 'plaza']
        if any(m in address_lower for m in mall_indicators):
            result['needs_review'] = True
            result['decision_friction'] = 2
            result['friction_reason'] = 'mall_location'
            result['corporate_reason'] = 'Located in mall/shopping center'
            result['category'] = 'review'
            return result

        # =====================================================================
        # LAYER E: High Review Count Heuristic
        # =====================================================================
        if rating_count > 5000:
            result['needs_review'] = True
            result['decision_friction'] = 1
            result['friction_reason'] = 'high_volume_check'
            result['category'] = 'review'
            return result

        # =====================================================================
        # LAYER F: Franchise Name Patterns
        # =====================================================================
        franchise_patterns = [
            r'\b(franchise|franchis)\b',
            r'\blocation\s*\d+',
            r'\bunit\s*\d+',
            r'\bstore\s*#?\d+',
            r'#\d{3,}',  # Store numbers like #1234
        ]
        for pattern in franchise_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                result['corporate_likely'] = True
                result['corporate_reason'] = f"Franchise naming pattern"
                result['decision_friction'] = 3
                result['friction_reason'] = 'franchise_naming'
                result['category'] = 'corporate'
                return result

        # =====================================================================
        # Default: Likely Independent
        # =====================================================================
        result['decision_friction'] = 0
        result['friction_reason'] = 'independent'
        result['category'] = 'closeable'

        return result


# ============================================================================
# Google Places API Client
# ============================================================================

class GooglePlacesClient:
    BASE_URL = "https://places.googleapis.com/v1"
    GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    def __init__(self, api_key: str, cache_dir: str, rate_limiter: RateLimiter):
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.rate_limiter = rate_limiter
        self.session = requests.Session()

    def geocode(self, address: str) -> Optional[tuple[float, float]]:
        cache_key = f"geocode:{address}"
        cache_path = get_cache_path(self.cache_dir, cache_key)

        cached = load_from_cache(cache_path)
        if cached:
            return cached.get('lat'), cached.get('lng')

        self.rate_limiter.wait()

        try:
            response = self.session.get(self.GEOCODE_URL, params={
                'address': address,
                'key': self.api_key
            })
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'OK' and data.get('results'):
                location = data['results'][0]['geometry']['location']
                result = {'lat': location['lat'], 'lng': location['lng']}
                save_to_cache(cache_path, result)
                return result['lat'], result['lng']
        except Exception as e:
            print(f"Geocoding error: {e}")
        return None

    def search_nearby(self, lat: float, lng: float, radius_m: int,
                      included_types: list, max_results: int = 20) -> list[dict]:
        cache_key = f"nearby:{lat:.6f},{lng:.6f}:{radius_m}:{','.join(sorted(included_types))}"
        cache_path = get_cache_path(self.cache_dir, cache_key)

        cached = load_from_cache(cache_path)
        if cached:
            return cached.get('places', [])

        self.rate_limiter.wait()

        url = f"{self.BASE_URL}/places:searchNearby"
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.types,places.rating,places.userRatingCount,places.priceLevel,places.internationalPhoneNumber,places.websiteUri,places.regularOpeningHours,places.location'
        }

        body = {
            'locationRestriction': {
                'circle': {
                    'center': {'latitude': lat, 'longitude': lng},
                    'radius': float(radius_m)
                }
            },
            'includedTypes': included_types,
            'maxResultCount': min(max_results, 20),
            'rankPreference': 'DISTANCE'
        }

        try:
            response = self.session.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            places = data.get('places', [])
            save_to_cache(cache_path, {'places': places})
            return places
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("Rate limited, waiting 60 seconds...")
                time.sleep(60)
                return self.search_nearby(lat, lng, radius_m, included_types, max_results)
            print(f"Places search error: {e}")
            return []
        except Exception as e:
            print(f"Places search error: {e}")
            return []

    def search_ev_chargers(self, lat: float, lng: float, radius_miles: int) -> list[dict]:
        """Search for EV chargers using Google Places."""
        print("Using Google Places for charger data...")

        radius_m = min(radius_miles * 1609.34, 50000)
        stations = []
        grid_size = 3
        step_miles = radius_miles / grid_size

        for i in range(-grid_size // 2, grid_size // 2 + 1):
            for j in range(-grid_size // 2, grid_size // 2 + 1):
                lat_offset = i * step_miles / 69.0
                lng_offset = j * step_miles / (69.0 * math.cos(math.radians(lat)))

                search_lat = lat + lat_offset
                search_lng = lng + lng_offset

                cache_key = f"chargers:{search_lat:.4f},{search_lng:.4f}"
                cache_path = get_cache_path(self.cache_dir, cache_key)

                cached = load_from_cache(cache_path)
                if cached:
                    stations.extend(cached.get('stations', []))
                    continue

                self.rate_limiter.wait()

                url = f"{self.BASE_URL}/places:searchNearby"
                headers = {
                    'Content-Type': 'application/json',
                    'X-Goog-Api-Key': self.api_key,
                    'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location'
                }

                body = {
                    'locationRestriction': {
                        'circle': {
                            'center': {'latitude': search_lat, 'longitude': search_lng},
                            'radius': min(step_miles * 1609.34, 50000)
                        }
                    },
                    'includedTypes': ['electric_vehicle_charging_station'],
                    'maxResultCount': 20,
                }

                try:
                    response = self.session.post(url, headers=headers, json=body)
                    response.raise_for_status()
                    data = response.json()

                    grid_stations = []
                    for place in data.get('places', []):
                        loc = place.get('location', {})
                        grid_stations.append({
                            'id': place.get('id', ''),
                            'station_name': place.get('displayName', {}).get('text', 'EV Charger'),
                            'latitude': loc.get('latitude'),
                            'longitude': loc.get('longitude'),
                        })

                    save_to_cache(cache_path, {'stations': grid_stations})
                    stations.extend(grid_stations)
                except Exception as e:
                    print(f"  Grid search error: {e}")

        # Deduplicate
        seen = set()
        unique = []
        for s in stations:
            if s['id'] not in seen:
                seen.add(s['id'])
                unique.append(s)

        print(f"Found {len(unique)} EV chargers")
        return unique


# ============================================================================
# NREL Client
# ============================================================================

class NRELClient:
    BASE_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1"

    def __init__(self, api_key: str, cache_dir: str, rate_limiter: RateLimiter):
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.rate_limiter = rate_limiter
        self.session = requests.Session()

    def search_stations(self, lat: float, lng: float, radius_miles: int) -> list[dict]:
        cache_key = f"nrel:{lat:.4f},{lng:.4f}:{radius_miles}"
        cache_path = get_cache_path(self.cache_dir, cache_key)

        cached = load_from_cache(cache_path)
        if cached:
            return cached.get('fuel_stations', [])

        self.rate_limiter.wait()

        params = {
            'api_key': self.api_key,
            'latitude': lat,
            'longitude': lng,
            'radius': radius_miles,
            'fuel_type': 'ELEC',
            'status': 'E',
            'limit': 500,
            'access': 'public',
        }

        try:
            response = self.session.get(f"{self.BASE_URL}/nearest.json", params=params)
            response.raise_for_status()
            data = response.json()
            stations = data.get('fuel_stations', [])
            save_to_cache(cache_path, {'fuel_stations': stations})
            print(f"Found {len(stations)} EV chargers from NREL")
            return stations
        except Exception as e:
            print(f"NREL API error: {e}")
            return []


# ============================================================================
# Merchant Data Structure
# ============================================================================

@dataclass
class Merchant:
    place_id: str
    name: str
    address: str
    phone: str
    website: str
    types: str
    rating: float
    user_ratings_total: int
    price_level: str
    open_now: str
    merchant_lat: float
    merchant_lng: float
    nearest_charger_id: str
    nearest_charger_name: str
    charger_lat: float
    charger_lng: float
    distance_to_charger_m: float
    walk_time_min: float
    corporate_likely: bool
    corporate_reason: str
    needs_review: bool
    decision_friction: int
    friction_reason: str
    category: str
    source: str = "google_places"
    discovered_via_chargers: str = ""


# ============================================================================
# Main Merchant Finder
# ============================================================================

class MerchantFinder:
    def __init__(self, config: Config):
        self.config = config

        self.google_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not self.google_api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY environment variable is required")

        self.nrel_api_key = os.getenv('NREL_API_KEY')

        places_limiter = RateLimiter(config.places_requests_per_second)
        nrel_limiter = RateLimiter(config.nrel_requests_per_second)

        self.places_client = GooglePlacesClient(
            self.google_api_key, config.cache_dir, places_limiter
        )

        if self.nrel_api_key:
            self.nrel_client = NRELClient(
                self.nrel_api_key, config.cache_dir, nrel_limiter
            )
            print("Using NREL API for charger data")
        else:
            self.nrel_client = None
            print("NREL_API_KEY not set, will use Google Places for chargers")

        self.classifier = CorporateClassifier(config.denylist_path)
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)

    def run(self):
        print("\n" + "=" * 60)
        print("MERCHANT FINDER V2 - Multi-Layer Corporate Detection")
        print("=" * 60)

        # Step 1: Geocode
        print(f"\n[1/6] Geocoding: {self.config.home_address}")
        home_coords = self.places_client.geocode(self.config.home_address)
        if not home_coords:
            raise ValueError(f"Could not geocode: {self.config.home_address}")
        home_lat, home_lng = home_coords
        print(f"      Coordinates: {home_lat:.6f}, {home_lng:.6f}")

        # Step 2: Fetch chargers
        print(f"\n[2/6] Fetching EV chargers within {self.config.charger_search_radius_miles} miles...")
        if self.nrel_client:
            chargers = self._fetch_nrel_chargers(home_lat, home_lng)
        else:
            chargers = self.places_client.search_ev_chargers(
                home_lat, home_lng, self.config.charger_search_radius_miles
            )
        print(f"      Found {len(chargers)} chargers")

        if not chargers:
            print("ERROR: No chargers found!")
            return

        # Step 3: Search merchants
        print(f"\n[3/6] Searching for merchants...")
        merchants_by_id = {}

        for i, charger in enumerate(chargers[:self.config.max_chargers]):
            if (i + 1) % 25 == 0:
                print(f"      Processed {i + 1}/{min(len(chargers), self.config.max_chargers)} chargers...")

            charger_lat = charger.get('latitude')
            charger_lng = charger.get('longitude')
            charger_id = str(charger.get('id', i))
            charger_name = charger.get('station_name', 'Unknown')

            if not charger_lat or not charger_lng:
                continue

            for place_type in self.config.merchant_types:
                places = self.places_client.search_nearby(
                    charger_lat, charger_lng,
                    self.config.merchant_search_radius_m,
                    [place_type],
                    self.config.max_merchants_per_charger
                )

                for place in places:
                    self._process_place(
                        place, charger_id, charger_name,
                        charger_lat, charger_lng, merchants_by_id
                    )

        all_merchants = list(merchants_by_id.values())
        print(f"      Found {len(all_merchants)} unique merchants")

        # Step 4: Filter
        print(f"\n[4/6] Filtering merchants...")
        walk_limit = self.config.walk_time_minutes

        with_phone = [m for m in all_merchants if m.phone]
        print(f"      With phone: {len(with_phone)}")

        # Filter out merchants at exact charger location (same property)
        valid_distance = [m for m in with_phone if m.distance_to_charger_m >= 20]
        print(f"      Not at charger location: {len(valid_distance)}")

        within_walk = [m for m in valid_distance if m.walk_time_min <= walk_limit]
        print(f"      Within {walk_limit} min walk: {len(within_walk)}")

        # Step 5: Split into categories
        print(f"\n[5/6] Categorizing merchants...")
        closeable = []
        review = []
        corporate = []

        for m in within_walk:
            if m.category == 'corporate' or m.corporate_likely:
                corporate.append(m)
            elif m.category == 'review' or m.needs_review:
                review.append(m)
            else:
                closeable.append(m)

        print(f"      Closeable (independents): {len(closeable)}")
        print(f"      Review needed: {len(review)}")
        print(f"      Corporate (do not call): {len(corporate)}")

        # Step 6: Rank and save
        print(f"\n[6/6] Ranking and saving...")

        def rank_score(m: Merchant) -> tuple:
            score = m.rating * math.log1p(m.user_ratings_total) if m.rating else 0
            return (m.decision_friction, m.walk_time_min, -score)

        closeable.sort(key=rank_score)
        review.sort(key=rank_score)

        top_closeable = closeable[:self.config.top_n_merchants]

        self._save_csv(top_closeable, f"{self.config.output_dir}/merchants_closeable.csv")
        self._save_json(top_closeable, f"{self.config.output_dir}/merchants_closeable.json")
        self._save_csv(review[:200], f"{self.config.output_dir}/merchants_review.csv")
        self._save_csv(corporate, f"{self.config.output_dir}/merchants_corporate.csv")

        print(f"\n" + "=" * 60)
        print("COMPLETE!")
        print("=" * 60)
        print(f"\nOutputs in {self.config.output_dir}/:")
        print(f"  - merchants_closeable.csv ({len(top_closeable)} merchants)")
        print(f"  - merchants_closeable.json")
        print(f"  - merchants_review.csv ({min(len(review), 200)} merchants)")
        print(f"  - merchants_corporate.csv ({len(corporate)} merchants)")

    def _fetch_nrel_chargers(self, lat: float, lng: float) -> list[dict]:
        stations = self.nrel_client.search_stations(
            lat, lng, self.config.charger_search_radius_miles
        )
        return [{
            'id': s.get('id'),
            'station_name': s.get('station_name', 'Unknown'),
            'latitude': s.get('latitude'),
            'longitude': s.get('longitude'),
        } for s in stations]

    def _process_place(self, place: dict, charger_id: str, charger_name: str,
                       charger_lat: float, charger_lng: float, merchants: dict):
        place_id = place.get('id', '')
        if not place_id:
            return

        location = place.get('location', {})
        merchant_lat = location.get('latitude')
        merchant_lng = location.get('longitude')

        if not merchant_lat or not merchant_lng:
            return

        distance_m = haversine_distance(merchant_lat, merchant_lng, charger_lat, charger_lng)
        walk_min = walk_time_minutes(distance_m, self.config.walk_speed_mps)

        if walk_min > self.config.walk_time_minutes * 1.5:
            return

        name = place.get('displayName', {}).get('text', 'Unknown')
        address = place.get('formattedAddress', '')
        phone = place.get('internationalPhoneNumber', '')
        website = place.get('websiteUri', '')
        types = place.get('types', [])
        rating = place.get('rating', 0)
        rating_count = place.get('userRatingCount', 0)
        price_level = place.get('priceLevel', '')

        hours = place.get('regularOpeningHours', {})
        open_now = 'yes' if hours.get('openNow') else 'no' if hours else 'unknown'

        # Multi-layer classification
        classification = self.classifier.classify(
            name, types, website, rating_count, address
        )

        if place_id in merchants:
            existing = merchants[place_id]
            if distance_m < existing.distance_to_charger_m:
                existing.nearest_charger_id = charger_id
                existing.nearest_charger_name = charger_name
                existing.charger_lat = charger_lat
                existing.charger_lng = charger_lng
                existing.distance_to_charger_m = distance_m
                existing.walk_time_min = walk_min
            charger_ids = set(existing.discovered_via_chargers.split(',')) if existing.discovered_via_chargers else set()
            charger_ids.add(charger_id)
            existing.discovered_via_chargers = ','.join(charger_ids)
        else:
            merchants[place_id] = Merchant(
                place_id=place_id,
                name=name,
                address=address,
                phone=phone,
                website=website,
                types=','.join(types),
                rating=rating,
                user_ratings_total=rating_count,
                price_level=str(price_level) if price_level else '',
                open_now=open_now,
                merchant_lat=merchant_lat,
                merchant_lng=merchant_lng,
                nearest_charger_id=charger_id,
                nearest_charger_name=charger_name,
                charger_lat=charger_lat,
                charger_lng=charger_lng,
                distance_to_charger_m=round(distance_m, 1),
                walk_time_min=round(walk_min, 2),
                corporate_likely=classification['corporate_likely'],
                corporate_reason=classification['corporate_reason'],
                needs_review=classification['needs_review'],
                decision_friction=classification['decision_friction'],
                friction_reason=classification['friction_reason'],
                category=classification['category'],
                discovered_via_chargers=charger_id
            )

    def _save_csv(self, merchants: list[Merchant], path: str):
        if not merchants:
            print(f"      No merchants to save to {path}")
            return

        fieldnames = list(asdict(merchants[0]).keys())

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for m in merchants:
                writer.writerow(asdict(m))

        print(f"      Saved {len(merchants)} to {path}")

    def _save_json(self, merchants: list[Merchant], path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump([asdict(m) for m in merchants], f, indent=2)


def main():
    config = Config()

    if os.getenv('HOME_ADDRESS'):
        config.home_address = os.getenv('HOME_ADDRESS')
    if os.getenv('CHARGER_RADIUS_MILES'):
        config.charger_search_radius_miles = int(os.getenv('CHARGER_RADIUS_MILES'))
    if os.getenv('WALK_TIME_MINUTES'):
        config.walk_time_minutes = int(os.getenv('WALK_TIME_MINUTES'))

    try:
        finder = MerchantFinder(config)
        finder.run()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
