# app/services/merchants_google.py
import os
import urllib.parse
import requests

API_KEY = "AIzaSyAs0PVYXj3-ztRXCjdd0ztUGUSjQR73FFg"

# map Google primary/secondary types → our categories
TYPE_MAP = {
    "restaurant": "dining_sitdown",
    "meal_takeaway": "quick_bite",
    "cafe": "coffee_bakery",
    "bar": "dining_sitdown",
    "shopping_mall": "shopping_retail",
    "clothing_store": "shopping_retail",
    "department_store": "shopping_retail",
    "supermarket": "shopping_retail",
}

def _badge(types):
    for t in types or []:
        if t in TYPE_MAP:
            return TYPE_MAP[t].split("_")[0].capitalize()
    return "Other"

def _category_list(types):
    cats = []
    for t in types or []:
        if t in TYPE_MAP and TYPE_MAP[t] not in cats:
            cats.append(TYPE_MAP[t])
    return cats or ["other"]

def _dd_link(name: str, lat: float, lng: float, hub_id: str):
    q = urllib.parse.quote(name)
    return f"https://www.doordash.com/search/store/{q}/?lat={lat}&lng={lng}&utm_source=nerava&utm_medium=app&utm_campaign={hub_id}"

def _ot_link(name: str, lat: float, lng: float, hub_id: str):
    q = urllib.parse.quote(name)
    return f"https://www.opentable.com/s?covers=2&currentlocationid=0&latitude={lat}&longitude={lng}&term={q}&utm_source=nerava&utm_medium=app&utm_campaign={hub_id}"

def search_nearby(*, lat: float, lng: float, radius_m: int = 600, prefs=None, limit: int = 12, hub_id: str = "hub_unknown"):
    if not API_KEY:
        return []
    # Places Nearby (new) – fields kept minimal for speed
    url = (
        "https://places.googleapis.com/v1/places:searchNearby"
    )
    payload = {
        "includedTypes": ["restaurant","cafe","meal_takeaway","shopping_mall","clothing_store","department_store","supermarket","bar","tourist_attraction","movie_theater","book_store","gym"],
        "maxResultCount": min(20, max(1, limit)),
        "locationRestriction": {
            "circle": {"center": {"latitude": lat, "longitude": lng}, "radius": radius_m}
        }
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.types,places.iconMaskBaseUri"
    }
    r = requests.post(url, json=payload, headers=headers, timeout=12)
    r.raise_for_status()
    data = r.json()
    places = data.get("places", []) or []

    # optional simple preference filtering (keeps items that match one of the pref buckets)
    prefs = set(prefs or [])
    out = []
    for p in places:
        name = p.get("displayName", {}).get("text")
        types = p.get("types", [])
        cats = _category_list(types)
        if prefs and not any(pref in cats for pref in prefs):
            # let a few through for variety
            pass
        badge = _badge(types)
        logo = (p.get("iconMaskBaseUri") or "").replace("pinlet_v2","pinlet")
        item = {
            "name": name,
            "badge": badge,
            "categories": cats,
            "logo": logo if logo else "https://maps.gstatic.com/mapfiles/place_api/icons/v2/generic_pinlet",
            "distance_hint": "walkable",
            "links": {
                "pickup": _dd_link(name, lat, lng, hub_id),
                "reserve": _ot_link(name, lat, lng, hub_id),
            }
        }
        out.append(item)
        if len(out) >= limit:
            break
    return out
