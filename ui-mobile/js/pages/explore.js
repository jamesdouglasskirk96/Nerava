/**
 * Explore Page - Apple Maps-style redesign
 * 
 * FILE STRUCTURE:
 * - HTML: ui-mobile/index.html (lines 84-179: #page-explore section)
 * - JS: ui-mobile/js/pages/explore.js (this file)
 * - Map Core: ui-mobile/js/core/map.js (Leaflet-based map utilities)
 * 
 * DATA SOURCES:
 * - Merchants/Perks: /v1/drivers/merchants/nearby (v1 API, zone-scoped)
 * - User location: navigator.geolocation API
 * 
 * NEW STRUCTURE (Apple Maps-style):
 * - Full-screen map background
 * - Top overlay: SearchBar + SuggestionsRow
 * - Right-side controls: Locate me + Filters
 * - AirDrop-style popover: Merchant quick view on tap (shown on charger/merchant tap)
 */

import Api, { 
  apiNearbyMerchants, 
  apiJoinChargeEvent, 
  getCurrentUser,
  EVENT_SLUG,
  ZONE_SLUG,
  apiRedeemNova,
  apiWalletSummary,
  apiChargerDiscovery,
} from '../core/api.js';
import { ensureMap, clearStations, addStationDot, fitToStations, getMap } from '../core/map.js';
import { setTab } from '../app.js';
import { getOptimalChargingTime, getChargingStateDisplay, getChargingState } from '../core/charging-state.js';
import { createModal, showModal } from '../components/modal.js';
import { openMerchantDetail } from './merchant-detail.js';

// Leaflet reference (assumes L is global from Leaflet script)
const L = window.L;

const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));

// Use local placeholder for all merchant logos to avoid 403s from third-party domains
// Temporarily using data URI to avoid loading avatar-default.png
const MERCHANT_LOGO_PLACEHOLDER = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

// === Recommended Perks Data =====================================
// Three perks: Starbucks, Target, Whole Foods
const _recommendedPerks = [
  {
    id: 'perk_1',
    name: "Starbucks",
    logo: MERCHANT_LOGO_PLACEHOLDER,
    nova: 12,
    walk: "3 min walk"
  },
  {
    id: 'perk_2',
    name: "Target",
    logo: MERCHANT_LOGO_PLACEHOLDER,
    nova: 8,
    walk: "5 min walk"
  },
  {
    id: 'perk_3',
    name: "Whole Foods",
    logo: MERCHANT_LOGO_PLACEHOLDER,
    nova: 10,
    walk: "7 min walk"
  }
];

// === Explore: Next Charger Micro-State =====================================
const CHARGER_FALLBACK = [
  { id: 'hub_arboretum', name:'Arboretum Supercharger', addr:'9722 Great Hills Trl, Austin, TX', lat:30.3996, lng:-97.7472, merchant:{name:'Starbucks', logo:MERCHANT_LOGO_PLACEHOLDER}, perk:'Free coffee 2–4pm • 3 min walk' },
  { id: 'hub_domain',     name:'Domain Northside',      addr:'11821 Rock Rose Ave, Austin, TX', lat:30.4019, lng:-97.7251, merchant:{name:'Neiman Marcus', logo:MERCHANT_LOGO_PLACEHOLDER}, perk:'10% off with charge • 4 min walk' },
  { id: 'hub_dt',         name:'Downtown 5th & Lavaca', addr:'500 Lavaca St, Austin, TX',       lat:30.2676, lng:-97.7429, merchant:{name:'Starbucks', logo:MERCHANT_LOGO_PLACEHOLDER}, perk:'Free coffee 2–4pm • 3 min walk' }
];

const FALLBACK_HUB = {
  hub_id: 'domain',
  hub_name: 'Domain – Austin',
};

function normalizeNumber(n) {
  const parsed = Number(n);
  if (Number.isNaN(parsed)) return 0;
  return Math.round(parsed);
}

function toMapCharger(charger) {
  if (!charger) return null;
  return {
    id: charger.id || `charger_${charger.lat}_${charger.lng}`,
    name: charger.name || 'Charger',
    lat: Number(charger.lat),
    lng: Number(charger.lng),
    network: charger.network_name || charger.network || 'Domain Hub',
    distance_m: normalizeNumber(charger.distance_m || 0),
    walk_time_s: normalizeNumber(charger.walk_time_s || 0),
  };
}

function toMapMerchant(merchant) {
  console.log('[Explore] Mapping merchant:', merchant);
  if (!merchant) {
    console.warn('[Explore] Merchant is null/undefined, skipping');
    return null;
  }
  
  // Check for lat/lng - these are required
  if (merchant.lat === undefined || merchant.lat === null || merchant.lng === undefined || merchant.lng === null) {
    console.warn('[Explore] Merchant missing lat/lng:', { id: merchant.id, name: merchant.name, lat: merchant.lat, lng: merchant.lng });
  }
  
  const walkTime = normalizeNumber(merchant.walk_time_s || merchant.walk_seconds || 0);
  
  // Preserve logo_url from API response (could be null, empty, or a URL)
  const logoUrl = merchant.logo_url || merchant.logo || null;
  
  const mappedMerchant = {
    id: merchant.id || merchant.merchant_id || `merchant_${Math.random().toString(36).slice(2)}`,
    name: merchant.name || 'Merchant',
    lat: Number(merchant.lat),
    lng: Number(merchant.lng),
    category: merchant.category || 'other',
    distance_m: normalizeNumber(merchant.distance_m || 0),
    walk_time_s: walkTime,
    nova_reward: normalizeNumber(merchant.nova_reward || merchant.total_nova_awarded || 0),
    logo: logoUrl, // Keep null if missing (don't use empty string)
    logo_url: logoUrl, // Also preserve as logo_url for compatibility
    raw: merchant,
  };
  
  console.log('[Explore] Mapped merchant result:', mappedMerchant);
  return mappedMerchant;
}

function merchantToPerkCard(merchant) {
  const walkMinutes = merchant.walk_time_s
    ? Math.max(1, Math.round(merchant.walk_time_s / 60))
    : merchant.distance_m
    ? `${merchant.distance_m} m walk`
    : 'Walkable';
  // Only use logo_url if it exists (no fallback - show no logo if missing)
  const logo = merchant.logo || merchant.logo_url || null;
  
  return {
    id: merchant.id,
    name: merchant.name,
    logo: logo, // null or undefined if no logo - frontend will handle gracefully
    nova: normalizeNumber(merchant.nova_reward || merchant.nova || 0),
    nova_reward: normalizeNumber(merchant.nova_reward || merchant.nova || 0), // Keep both for compatibility
    walk: typeof walkMinutes === 'string' ? walkMinutes : `${walkMinutes} min walk`,
  };
}

function renderChargerPins(chargers) {
  clearStations();
  chargers.forEach(ch => {
    addStationDot(ch, { onClick: () => selectCharger(ch) });
  });
  
  // Fit map to show all chargers with padding for perk cards
  if (_map && chargers.length > 0 && typeof L !== 'undefined') {
    // Calculate bounds from all charger positions
    const chargerPositions = chargers.map(c => [c.lat, c.lng]);
    
    // Estimate perk card height (approximately 260px including padding)
    const perksPanelHeight = 260;
    
    // Use Leaflet fitBounds with padding
    const bounds = L.latLngBounds(chargerPositions);
    _map.fitBounds(bounds, {
      paddingTopLeft: [16, 16],
      paddingBottomRight: [16, perksPanelHeight + 32], // Extra padding for perk cards
      maxZoom: 17 // Prevent excessive zoom
    });
  } else {
    // Fallback to fitToStations if map not ready or Leaflet not available
    fitToStations(chargers);
  }
}

function renderMerchantPins(merchants) {
  clearStations();
  if (!merchants || merchants.length === 0) {
    return;
  }
  
  merchants.forEach(merchant => {
    // Use merchant lat/lng for pin location
    if (merchant.lat && merchant.lng) {
      const merchantStation = {
        lat: merchant.lat,
        lng: merchant.lng,
        network: 'merchant',
        status: 'available',
        name: merchant.name,
        id: merchant.id
      };
      addStationDot(merchantStation, { 
        onClick: () => selectMerchant(merchant) 
      });
    }
  });
  
  // Fit map to show all merchants with padding
  if (_map && merchants.length > 0 && typeof L !== 'undefined') {
    const merchantPositions = merchants
      .filter(m => m.lat && m.lng)
      .map(m => [m.lat, m.lng]);
    
    if (merchantPositions.length > 0) {
      const bounds = L.latLngBounds(merchantPositions);
      _map.fitBounds(bounds, {
        paddingTopLeft: [16, 16],
        paddingBottomRight: [16, 32],
        maxZoom: 17
      });
    }
  } else if (merchants.length > 0) {
    const stations = merchants
      .filter(m => m.lat && m.lng)
      .map(m => ({ lat: m.lat, lng: m.lng }));
    fitToStations(stations);
  }
}

function selectMerchant(merchant) {
  _selectedMerchantId = merchant.id;
  _selectedMerchant = merchant;
  
  console.log('Merchant tapped:', merchant.id, merchant.name);
  
  // Center map on merchant
  if (_map && merchant.lat && merchant.lng) {
    _map.setView([merchant.lat, merchant.lng], 15);
  }
  
  // Don't show popover - navigate directly to merchant detail instead
  openMerchantDetail(merchant);
}

// === State Management ======================================================
let _chargers = [];
let _merchants = [];
let _selectedChargerId = null;
let _selectedMerchantId = null;
let _selectedMerchant = null; // Store full merchant object
let _selectedCharger = null; // Store selected charger object
let _selectedCategory = null;
let _selectedWhileYouCharge = false; // For "While you charge" filter
let _userLocation = null;
let _map = null;
let _pilotBootstrap = null;
let _pilotMode = true;
let _activeQuery = '';

function fallbackChargers() {
  return CHARGER_FALLBACK.map(c => ({
    id: c.id,
    name: c.name,
    lat: c.lat,
    lng: c.lng,
    network: 'Tesla',
    distance_m: 0,
    walk_time_s: 0,
  }));
}

// Default Domain Austin location (near Eggman at 1720 Barton Springs Rd)
const DEFAULT_LAT = 30.2634382;
const DEFAULT_LNG = -97.7628908;

async function loadPilotData() {
  showLoadingState();
  try {
    // Get user location for nearby merchants query
    // Default Domain Austin location (near Eggman)
    let userLat = DEFAULT_LAT;
    let userLng = DEFAULT_LNG;
    
    try {
      if (_userLocation?.lat && _userLocation?.lng) {
        userLat = _userLocation.lat;
        userLng = _userLocation.lng;
        console.log('[Explore] Using user location:', { lat: userLat, lng: userLng });
      } else {
        console.warn('[Explore] Using default location:', { lat: DEFAULT_LAT, lng: DEFAULT_LNG });
      }
    } catch (e) {
      console.warn('[Explore] Error getting user location, using default:', e);
      console.warn('[Explore] Using default location:', { lat: DEFAULT_LAT, lng: DEFAULT_LNG });
    }
    
    // Load chargers from API discovery endpoint (shows all seeded chargers)
    console.log('[Explore] Loading chargers from discovery API:', { lat: userLat, lng: userLng });
    try {
      const discoveryData = await apiChargerDiscovery({ lat: userLat, lng: userLng });
      console.log('[Explore] Discovery API response:', discoveryData);
      
      if (discoveryData && discoveryData.chargers && Array.isArray(discoveryData.chargers)) {
        _chargers = discoveryData.chargers.map(toMapCharger).filter(Boolean);
        console.log('[Explore] Loaded', _chargers.length, 'chargers from API');
      } else {
        console.warn('[Explore] Invalid discovery response, using fallback');
        _chargers = fallbackChargers();
      }
    } catch (err) {
      console.error('[Explore] Error fetching chargers from API:', err);
      console.warn('[Explore] Falling back to hardcoded chargers');
      _chargers = fallbackChargers();
    }
    
    // Load nearby merchants using v1 API
    // Use a larger radius to include all merchants in the zone (Domain area spans ~15km)
    console.log('[Explore] Loading merchants with params:', { lat: userLat, lng: userLng, zoneSlug: ZONE_SLUG, radiusM: 20000, novaOnly: true });
    let merchantsRaw;
    try {
      const merchantsRes = await apiNearbyMerchants({
        zoneSlug: ZONE_SLUG,
        lat: userLat,
        lng: userLng,
        radiusM: 20000, // Increased to 20km to include all Domain area merchants
        novaOnly: true, // Always fetch Nova-accepting merchants
      });
      console.log('[Explore] Raw API response:', merchantsRes);
      console.log('[Explore] Response type:', typeof merchantsRes, Array.isArray(merchantsRes));
      merchantsRaw = Array.isArray(merchantsRes) ? merchantsRes : [];
    } catch (err) {
      console.error('[Explore] Error fetching nearby merchants:', err);
      merchantsRaw = []; // Fallback to empty array
    }
    console.log('[Explore] Raw merchants from API:', merchantsRaw.length, merchantsRaw);
    
    // Log first merchant's structure to debug logo_url
    if (merchantsRaw.length > 0) {
      const firstMerchant = merchantsRaw[0];
      console.log('[Explore] === FIRST MERCHANT DEBUG ===');
      console.log('[Explore] Merchant name:', firstMerchant.name);
      console.log('[Explore] Merchant ID:', firstMerchant.id);
      console.log('[Explore] All merchant fields:', Object.keys(firstMerchant));
      console.log('[Explore] logo_url value:', firstMerchant.logo_url);
      console.log('[Explore] photo_url value:', firstMerchant.photo_url);
      console.log('[Explore] Full merchant object:', JSON.stringify(firstMerchant, null, 2));
      console.log('[Explore] === END FIRST MERCHANT DEBUG ===');
    }
    
    _merchants = merchantsRaw.map(toMapMerchant).filter(Boolean);
    console.log('[Explore] Mapped merchants:', _merchants.length, _merchants);
    
    // Sort merchants by distance_to_charger_m ascending
    _merchants.sort((a, b) => {
      const distA = a.distance_to_charger_m ?? Infinity;
      const distB = b.distance_to_charger_m ?? Infinity;
      return distA - distB;
    });
    
    // Render merchant pins on map (using merchant locations, not charger locations)
    renderMerchantPins(_merchants);
    
    // Convert merchants to Resy-style format and render
    if (_merchants.length > 0) {
      const merchantCards = _merchants.map(m => ({
        ...m,
        rating: m.rating || 4.6,
        rating_count: m.rating_count || 2500,
        price_tier: m.price_tier || '$$',
        distance_text: m.distance_text || (m.walk_time_s ? `${Math.round(m.walk_time_s / 60)} min` : '0.1 mi'),
        image_url: m.image_url || m.photo_url || m.logo_url,
      }));
      updateRecommendedPerks(merchantCards);
    }
    
    // Log first mapped merchant to see logo field
    if (_merchants.length > 0) {
      const firstMapped = _merchants[0];
      console.log('[Explore] === FIRST MAPPED MERCHANT DEBUG ===');
      console.log('[Explore] Mapped merchant name:', firstMapped.name);
      console.log('[Explore] Mapped merchant logo field:', firstMapped.logo);
      console.log('[Explore] Mapped merchant logo_url field:', firstMapped.logo_url);
      console.log('[Explore] === END FIRST MAPPED MERCHANT DEBUG ===');
    }
    
    // Merchants already sorted by distance_to_charger_m above

    // Check if coming from Wallet redeem flow - AFTER merchants are loaded
    const hasRedeemIntent = sessionStorage.getItem('nerava_redeem_intent') === 'true';
    if (hasRedeemIntent && _merchants.length > 0) {
      sessionStorage.removeItem('nerava_redeem_intent');
      console.log('[Explore] Redeem intent detected, auto-selecting from', _merchants.length, 'merchants');
      autoSelectClosestMerchant();
    } else if (hasRedeemIntent && _merchants.length === 0) {
      console.warn('[Explore] Redeem intent but no merchants loaded!');
      showToast('No merchants available');
      sessionStorage.removeItem('nerava_redeem_intent');
    }

    if (_merchants.length) {
      // Merchants already loaded and sorted, no need to filter
    } else {
      // Fallback to default perks if no merchants found
      _merchants = _recommendedPerks.map(perk => ({
        id: perk.id,
        name: perk.name,
        logo_url: perk.logo,
        nova_reward: perk.nova,
        walk_time_s: 0,
      }));
      // Convert perks to merchant format for Resy cards
      const merchantCards = _recommendedPerks.map(p => ({
        id: p.id,
        name: p.name,
        rating: 4.6,
        rating_count: 2500,
        category: 'Food & Drink',
        price_tier: '$$',
        distance_text: p.walk || '0.1 mi',
        image_url: p.logo,
      }));
      updateRecommendedPerks(merchantCards);
    }

    // Render charger pins on map
    if (_chargers.length > 0) {
      renderChargerPins(_chargers);
      selectCharger(_chargers[0]);
    }
  } catch (err) {
    console.error('[Explore] Failed to load merchants (v1):', err);
    _chargers = fallbackChargers();
    _merchants = _recommendedPerks.map(perk => ({
      id: perk.id,
      name: perk.name,
      logo_url: perk.logo,
      nova_reward: perk.nova,
      walk_time_s: 0,
    }));
    // Convert perks to merchant format for Resy cards
    const merchantCards = _recommendedPerks.map(p => ({
      id: p.id,
      name: p.name,
      rating: 4.6,
      rating_count: 2500,
      category: 'Food & Drink',
      price_tier: '$$',
      distance_text: p.walk || '0.1 mi',
      image_url: p.logo,
    }));
    updateRecommendedPerks(merchantCards);
    showEmptyState('Failed to load merchants – please try again.');

    // Render charger pins on map
    if (_chargers.length > 0) {
      renderChargerPins(_chargers);
      selectCharger(_chargers[0]);
    }
  }
}

// Fetch merchants with filters from backend
async function fetchMerchantsWithFilters(query = '', category = null, whileYouCharge = false) {
  showLoadingState();
  
  try {
    // Get user location
    let userLat = DEFAULT_LAT;
    let userLng = DEFAULT_LNG;
    
    if (_userLocation?.lat && _userLocation?.lng) {
      userLat = _userLocation.lat;
      userLng = _userLocation.lng;
    }
    
    // Build API params
    const params = {
      zoneSlug: ZONE_SLUG,
      lat: userLat,
      lng: userLng,
      radiusM: 20000, // Increased to 20km to include all Domain area merchants
      novaOnly: true,
    };
    
    if (query && query.trim()) {
      params.q = query.trim();
    }
    
    if (category) {
      params.category = category;
    }
    
    if (whileYouCharge) {
      params.while_you_charge = true;
    }
    
    console.log('[Explore] Fetching merchants with filters:', params);
    
    const merchantsRes = await apiNearbyMerchants(params);
    const merchantsRaw = Array.isArray(merchantsRes) ? merchantsRes : [];
    
    _merchants = merchantsRaw.map(toMapMerchant).filter(Boolean);
    
    // Sort by distance_to_charger_m ascending
    _merchants.sort((a, b) => {
      const distA = a.distance_to_charger_m ?? Infinity;
      const distB = b.distance_to_charger_m ?? Infinity;
      return distA - distB;
    });
    
    // Update map pins
    renderMerchantPins(_merchants);
    
    // Update UI
    if (_merchants.length > 0) {
      const merchantCards = _merchants.map(m => ({
        ...m,
        rating: m.rating || 4.6,
        rating_count: m.rating_count || 2500,
        price_tier: m.price_tier || '$$',
        distance_text: m.distance_text || (m.walk_time_s ? `${Math.round(m.walk_time_s / 60)} min` : '0.1 mi'),
        image_url: m.image_url || m.photo_url || m.logo_url,
      }));
      
      // Center map on first merchant (the one that will be shown in the bottom card)
      const firstMerchant = _merchants[0];
      if (_map && firstMerchant && firstMerchant.lat && firstMerchant.lng) {
        _map.setView([firstMerchant.lat, firstMerchant.lng], 15);
        console.log('[Explore] Centered map on first merchant after search/filter:', firstMerchant.name);
      }
      
      updateRecommendedPerks(merchantCards);
      
      // Update list view if expanded
      const sheet = $('#explore-list-sheet');
      if (sheet && sheet.classList.contains('expanded')) {
        renderMerchantList(_merchants);
      }
    } else {
      showEmptyState('No matching merchants');
    }
  } catch (err) {
    console.error('[Explore] Failed to fetch merchants with filters:', err);
    showEmptyState('Failed to load merchants – please try again.');
  }
}

// Toast helper
function showToast(message) {
  const toast = document.createElement('div');
  toast.style.cssText = 'position:fixed;left:50%;bottom:100px;transform:translateX(-50%);background:#111;color:#fff;padding:10px 14px;border-radius:12px;z-index:9999;font-weight:700';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// === Search Bar ============================================================
let _searchTimeout = null;

function initSearchBar() {
  const searchInput = $('#explore-search-input');
  const voiceBtn = $('#explore-voice-btn');
  
  if (!searchInput) return;
  
  // Text search - debounced API call
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    
    // Clear previous timeout
    if (_searchTimeout) {
      clearTimeout(_searchTimeout);
    }
    
    // Debounce: wait 300ms after user stops typing
    _searchTimeout = setTimeout(async () => {
      console.log(`[Explore] Searching merchants by query: "${query}"`);
      _activeQuery = query;
      await fetchMerchantsWithFilters(query, _selectedCategory, _selectedWhileYouCharge);
    }, 300);
  });
  
  // Enter key triggers immediate search
  searchInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (_searchTimeout) {
        clearTimeout(_searchTimeout);
      }
      
      const query = searchInput.value.trim();
      _activeQuery = query;
      await fetchMerchantsWithFilters(query, _selectedCategory, _selectedWhileYouCharge);
    }
  });
  
  // Voice search (TODO: implement voice recognition)
  if (voiceBtn) {
    voiceBtn.addEventListener('click', () => {
      console.log('[Explore] Voice search clicked');
      showToast('Voice search coming soon');
    });
  }
}

// === Suggestions Chips =====================================================
function initSuggestions() {
  const chips = $$('.suggestion-chip');
  
  chips.forEach(chip => {
    chip.addEventListener('click', async () => {
      // Toggle active state
      const wasActive = chip.classList.contains('active');
      chips.forEach(c => c.classList.remove('active'));
      
      const category = chip.dataset.category;
      const filter = chip.dataset.filter;
      
      if (wasActive) {
        // Deselecting
        _selectedCategory = null;
        _selectedWhileYouCharge = false;
      } else {
        // Selecting
        chip.classList.add('active');
        
        if (filter === 'while_you_charge') {
          _selectedCategory = null;
          _selectedWhileYouCharge = true;
        } else if (category) {
          _selectedCategory = category;
          _selectedWhileYouCharge = false;
        }
      }
      
      // Fetch merchants with new filters
      await fetchMerchantsWithFilters(_activeQuery, _selectedCategory, _selectedWhileYouCharge);
    });
  });
}

// === Charge Chip ==============================================
function updateChargeChip() {
  const chip = $('#charge-chip');
  if (!chip) return;

  const chipText = chip.querySelector('.charge-chip__text');
  if (!chipText) return;

  const { state, nextChangeTime } = getChargingState();
  const stateDisplay = getChargingStateDisplay();
  
  // Update icon
  const iconEl = chip.querySelector('.charge-chip__icon');
  if (iconEl) iconEl.textContent = stateDisplay.icon;

  let label = '';
  const now = new Date();
  const diffMs = nextChangeTime - now;
  const hours = Math.max(1, Math.round(diffMs / (1000 * 60 * 60)));
  
  if (state === 'off-peak') {
    label = `Charge now, off-peak ends in ${hours}h`;
  } else {
    label = `Next off-peak starts in ${hours}h`;
  }

  chipText.textContent = label;
  chip.style.display = 'inline-flex';
}

function initChargeChip() {
  updateChargeChip();
  // Update every minute
  setInterval(updateChargeChip, 60000);
}

// === Center Map Button ==============================================
function centerMapOnUser() {
  if (!_map) {
    _map = getMap();
  }
  
  if (!_map) {
    console.warn('[Explore] Map not available for centering');
    return;
  }

  // Try user location first, then fallback to charger or default
  let loc = _userLocation;
  
  if (!loc && _chargers && _chargers.length > 0) {
    // Use first charger as fallback
    loc = {
      lat: _chargers[0].lat,
      lng: _chargers[0].lng
    };
  }
  
  if (!loc) {
    // Default to Domain area
    loc = { lat: 30.4021, lng: -97.7266 };
  }

  _map.setView([loc.lat, loc.lng], 15);
  console.log('[Explore] Map centered on:', loc);
}

// Map center button removed
// function initMapCenterButton() {
//   const btn = $('#map-center-btn');
//   if (!btn) return;
//
//   btn.addEventListener('click', centerMapOnUser);
//   console.log('[Explore] Center map button initialized');
// }

// === Merchant Popover ======================================================
function initMerchantPopover() {
  const popover = $('#merchant-popover');
  const startBtn = $('#popover-start-session');
  const cancelBtn = $('#popover-cancel');
  const moreBtn = $('#popover-more-details');
  
  if (startBtn) {
    startBtn.addEventListener('click', async () => {
      await handleStartSession();
    });
  }
  
  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      hideMerchantPopover();
    });
  }
  
  
  // Click outside to close
  if (popover) {
    popover.addEventListener('click', (e) => {
      if (e.target === popover) {
        hideMerchantPopover();
      }
    });
  }
}

function showMerchantPopover(merchant, charger = null) {
  const popover = $('#merchant-popover');
  const logoEl = $('#popover-merchant-logo');
  const nameEl = $('#popover-merchant-name');
  const textEl = $('#popover-merchant-text');
  
  if (!popover) return;
  
  // Use provided charger or default to first charger
  const displayCharger = charger || _chargers[0] || null;
  const chargerName = displayCharger?.name || 'charger';
  
  // Get reward text
  const novaReward = merchant.nova_reward || merchant.nova || 0;
  const rewardText = novaReward > 0 ? `Earn ${novaReward} Nova` : 'Get perks while you charge';
  
  // Get merchant display info
  const merchantLogo = merchant.logo || merchant.logo_url || '';
  const merchantName = merchant.name || 'Merchant';
  
  if (logoEl) logoEl.src = merchantLogo;
  if (nameEl) nameEl.textContent = merchantName;
  if (textEl) textEl.textContent = `${rewardText} when you charge at ${chargerName} and visit ${merchantName}`;
  
  // Store full merchant and charger objects for session start
  _selectedMerchant = merchant;
  _selectedMerchantId = merchant.id;
  _selectedCharger = displayCharger;
  
  popover.style.display = 'block';
}

function hideMerchantPopover() {
  const popover = $('#merchant-popover');
  if (popover) {
    popover.style.display = 'none';
  }
  _selectedMerchantId = null;
  _selectedMerchant = null;
  _selectedCharger = null;
}

// === Auto-select closest merchant for redeem flow =====================================
function autoSelectClosestMerchant() {
  if (!_merchants || _merchants.length === 0) {
    showToast('No merchants available');
    return;
  }

  // Get user location (try geolocation API first, then fallback)
  let userLat = _userLocation?.lat;
  let userLng = _userLocation?.lng;
  
  // If no user location, try to get it from geolocation API
  if (!userLat || !userLng) {
    if (navigator.geolocation) {
      // Try to get current location synchronously (with timeout)
      const positionPromise = new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
          reject,
          { timeout: 2000, maximumAge: 60000 }
        );
      });
      
      // Use async approach - if we can't get location quickly, use default
      positionPromise.then(loc => {
        userLat = loc.lat;
        userLng = loc.lng;
        selectClosestMerchantToLocation(userLat, userLng);
      }).catch(() => {
        // Fallback to default location
        selectClosestMerchantToLocation(30.4021, -97.7266);
      });
      return; // Will continue in promise callback
    } else {
      // No geolocation API, use default
      userLat = 30.4021;
      userLng = -97.7266;
    }
  }
  
  selectClosestMerchantToLocation(userLat, userLng);
}

function selectClosestMerchantToLocation(userLat, userLng) {
  // Haversine distance function (more accurate than Euclidean for lat/lng)
  function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // Earth radius in meters
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distance in meters
  }

  // Find closest merchant to user location
  let closest = null;
  let minDist = Infinity;

  for (const m of _merchants) {
    const lat = m.lat;
    const lng = m.lng;
    if (lat && lng) {
      const dist = haversineDistance(userLat, userLng, lat, lng);
      if (dist < minDist) {
        minDist = dist;
        closest = m;
      }
    }
  }

  if (!closest) {
    showToast('No merchants found');
    return;
  }

  console.log('[Explore] Selected closest merchant:', closest.name, 'distance:', Math.round(minDist), 'm');
  // NOTE: Toast notification "Found closest" has been removed - no showToast call here

  // Store selection state (for highlighting)
  _selectedMerchant = closest;
  _selectedMerchantId = closest.id;

  // Pan map to merchant location and highlight it
  if (_map && closest.lat && closest.lng) {
    _map.setView([closest.lat, closest.lng], 15);
    // Wait a bit for map to pan, then highlight the merchant pin
    setTimeout(() => {
      // Re-render pins to highlight the selected one
      if (_merchants.length > 0) {
        renderMerchantPins(_merchants);
      }
    }, 500);
  }
  
  // Do NOT open merchant detail page - let user click on it if they want
}

// === Show merchant popover with redeem button =====================================
function showMerchantPopoverWithRedeem(merchant) {
  const popover = $('#merchant-popover');
  if (!popover) return;

  const logoEl = popover.querySelector('#popover-merchant-logo');
  const nameEl = popover.querySelector('#popover-merchant-name');
  const textEl = popover.querySelector('#popover-merchant-text');
  const actionBtn = popover.querySelector('#popover-start-session');

  const merchantLogo = merchant.logo_url || merchant.logo || '/icons/merchant-default.png';
  const merchantName = merchant.name || 'Merchant';

  if (logoEl) logoEl.src = merchantLogo;
  if (nameEl) nameEl.textContent = merchantName;
  if (textEl) textEl.textContent = `Redeem your Nova at ${merchantName}`;

  // Change button to "Redeem Nova"
  if (actionBtn) {
    // Clone button to remove existing event listeners
    const newBtn = actionBtn.cloneNode(true);
    actionBtn.parentNode.replaceChild(newBtn, actionBtn);
    newBtn.textContent = 'Redeem Nova';
    newBtn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      openRedeemConfirmModal(merchant);
    };
  }

  _selectedMerchant = merchant;
  _selectedMerchantId = merchant.id;

  popover.style.display = 'block';
}

// === Open redeem confirmation modal =====================================
async function openRedeemConfirmModal(merchant) {
  // Get current Nova balance from sessionStorage or fetch
  let novaBalance = parseInt(sessionStorage.getItem('nerava_nova_balance') || '0', 10);

  // If no cached balance, try to get from wallet summary
  if (!novaBalance) {
    try {
      const summary = await apiWalletSummary();
      novaBalance = summary.nova_balance || 0;
      sessionStorage.setItem('nerava_nova_balance', novaBalance.toString());
    } catch (e) {
      console.error('Failed to get balance:', e);
      showToast('Unable to load balance');
      return;
    }
  }

  // Calculate redemption amount (min of balance and merchant max, default 300 Nova)
  const maxRedeem = merchant.max_nova_redeem || 300;
  const novaToRedeem = Math.min(novaBalance, maxRedeem);
  const conversionRate = 10; // cents per Nova
  const usdValue = (novaToRedeem * conversionRate / 100).toFixed(2);

  if (novaToRedeem <= 0) {
    showToast('No Nova available to redeem');
    return;
  }

  // Create modal content
  const content = `
    <div style="text-align: center; padding: 16px 0;">
      <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">Redeeming at</div>
      <div style="font-size: 18px; font-weight: 600; color: #111827; margin-bottom: 24px;">${merchant.name}</div>
      
      <div style="background: #f1f5f9; border-radius: 12px; padding: 16px; margin-bottom: 24px;">
        <div style="font-size: 14px; color: #64748b;">You're redeeming</div>
        <div style="font-size: 32px; font-weight: 700; color: #1e40af;">${novaToRedeem} Nova</div>
        <div style="font-size: 16px; color: #22c55e; font-weight: 600;">Worth $${usdValue}</div>
      </div>
      
      <div style="font-size: 12px; color: #64748b; margin-bottom: 16px;">
        Show the confirmation screen to the merchant
      </div>
      
      <button id="confirm-redeem-btn" style="width: 100%; padding: 16px; background: #1e40af; color: white; border: none; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer;">
        Accept
      </button>
      <button id="cancel-redeem-btn" style="width: 100%; padding: 12px; background: transparent; color: #64748b; border: none; font-size: 14px; cursor: pointer; margin-top: 8px;">
        Cancel
      </button>
    </div>
  `;

  const modal = createModal('Confirm Redemption', content);
  modal.id = 'redeem-confirm-modal';
  showModal(modal);

  // Wire buttons
  modal.querySelector('#confirm-redeem-btn').onclick = async () => {
    await executeRedemption(merchant, novaToRedeem, modal);
  };

  modal.querySelector('#cancel-redeem-btn').onclick = () => {
    modal.close();
    modal.remove();
  };
}

// === Execute redemption =====================================
async function executeRedemption(merchant, novaAmount, modal) {
  const btn = modal.querySelector('#confirm-redeem-btn');
  btn.disabled = true;
  btn.textContent = 'Processing...';

  try {
    // Generate idempotency key
    const idempotencyKey = `redeem_${Date.now()}_${merchant.id}_${novaAmount}`;

    // Call redeem API
    const result = await apiRedeemNova(merchant.id, novaAmount, null, idempotencyKey);

    // Close modal
    modal.close();
    modal.remove();

    // Hide merchant popover
    hideMerchantPopover();

    // Dispatch wallet refresh event
    window.dispatchEvent(new CustomEvent('nerava:wallet:invalidate'));

    // Navigate to success/show-code page
    sessionStorage.setItem('nerava_redeem_success', JSON.stringify({
      merchant_name: merchant.name,
      nova_redeemed: novaAmount,
      new_balance: result.driver_balance,
      transaction_id: result.transaction_id
    }));

    window.location.hash = '#/code?merchant_id=' + merchant.id;

  } catch (error) {
    console.error('Redemption failed:', error);
    btn.disabled = false;
    btn.textContent = 'Accept';
    showToast('Redemption failed: ' + (error.message || 'Unknown error'));
  }
}

// === Perk Card Start Session Handler ======================================
// New handler for perk cards that navigates directly to Earn page
async function handlePerkCardStartSession(perk) {
  // Find the full merchant object from _merchants
  const fullMerchant = _merchants.find(m => m.id === perk.id) || perk;
  
  // Get current selected charger or default to first
  let currentCharger = null;
  if (_selectedChargerId) {
    currentCharger = _chargers.find(c => c.id === _selectedChargerId);
  }
  if (!currentCharger && _chargers.length > 0) {
    currentCharger = _chargers[0];
  }
  
  if (!currentCharger) {
    showToast('No charger available');
    return;
  }
  
  const merchantId = fullMerchant.id;
  const chargerId = currentCharger.id;
  
  // Get user location
  let userLat = 30.4021; // Domain default
  let userLng = -97.7266;
  
  try {
    if (navigator.geolocation && _userLocation) {
      userLat = _userLocation.lat;
      userLng = _userLocation.lng;
    } else {
      // Try to get current location
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 });
      });
      userLat = position.coords.latitude;
      userLng = position.coords.longitude;
    }
  } catch (e) {
    console.warn('Could not get user location, using defaults:', e);
  }
  
  // Show loading state
  showToast('Starting session...');
  
  try {
    // Call v1 API to join charge event and start session
    const session = await apiJoinChargeEvent({
      eventSlug: EVENT_SLUG,
      chargerId,
      merchantId,
      userLat,
      userLng,
    });
    
    const sessionId = session.session_id;
    
    // Store session in global state
    const sessionState = {
      session_id: sessionId,
      charger: currentCharger,
      merchant: fullMerchant,
      event_id: session.event_id || EVENT_SLUG,
    };
    
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.setItem('pilot_session', JSON.stringify(sessionState));
    }
    
    window.pilotSession = sessionState;
    
    // Expose session data for demo runner
    window.__neravaCurrentSessionId = sessionId;
    window.__neravaDemoChargerLocation = {
      lat: currentCharger.lat || 30.37665,
      lng: currentCharger.lng || -97.65168,
    };
    window.__neravaDemoMerchantLocation = {
      lat: fullMerchant.lat || 30.4021,
      lng: fullMerchant.lng || -97.7266,
    };
    window.__neravaDemoMerchantId = merchantId;
    
    console.log('[Explore] Session started (v1):', session);
    console.log('[Explore] Demo data exposed:', {
      sessionId: window.__neravaCurrentSessionId,
      chargerLocation: window.__neravaDemoChargerLocation,
      merchantLocation: window.__neravaDemoMerchantLocation,
    });
    
    // Navigate directly to Earn page
    navigateToEarn(sessionId, merchantId, chargerId);
    
  } catch (e) {
    console.error('[Explore] Failed to start session:', e);
    showToast(`Failed to start session: ${e.message || 'Unknown error'}`);
  }
}

// === Navigate to Earn Helper ==============================================
// Centralized navigation to Earn page - prevents double navigation
function navigateToEarn(sessionId, merchantId, chargerId) {
  if (!sessionId || !merchantId || !chargerId) {
    console.error('[Explore] Cannot navigate - missing required IDs', { sessionId, merchantId, chargerId });
    return;
  }
  
  // Single navigation call with all params
  location.hash = `#/earn?session_id=${encodeURIComponent(sessionId)}&merchant_id=${encodeURIComponent(merchantId)}&charger_id=${encodeURIComponent(chargerId)}`;
  
  // Set tab to Earn (app.js will handle the route)
  setTab('earn');
}

// === Start Session Handler (for popover) ===================================
async function handleStartSession() {
  const merchant = _selectedMerchant;
  const charger = _selectedCharger || _chargers[0];
  
  if (!merchant || !charger) {
    showToast('Missing merchant or charger info');
    return;
  }
  
  const merchantId = merchant.id;
  const chargerId = charger.id;
  
  if (!merchantId || !chargerId) {
    showToast('Invalid merchant or charger ID');
    return;
  }
  
  // Get user location
  let userLat = 30.4021; // Domain default
  let userLng = -97.7266;
  
  try {
    if (navigator.geolocation && _userLocation) {
      userLat = _userLocation.lat;
      userLng = _userLocation.lng;
    } else {
      // Try to get current location
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 });
      });
      userLat = position.coords.latitude;
      userLng = position.coords.longitude;
    }
  } catch (e) {
    console.warn('Could not get user location, using defaults:', e);
  }
  
  // Show loading state
  showToast('Starting session...');
  
  try {
    // Get user location for verify_dwell initialization
    let userLat = 30.4021; // Domain default
    let userLng = -97.7266;
    
    try {
      if (navigator.geolocation && _userLocation) {
        userLat = _userLocation.lat;
        userLng = _userLocation.lng;
      } else {
        const position = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 });
        });
        userLat = position.coords.latitude;
        userLng = position.coords.longitude;
      }
    } catch (e) {
      console.warn('[Explore] Could not get user location, using defaults:', e);
    }
    
    // Call v1 API to join charge event
    const session = await apiJoinChargeEvent({
      eventSlug: EVENT_SLUG,
      chargerId: charger.id,
      merchantId: merchant.id,
      userLat,
      userLng,
    });
    
    const sessionId = session.session_id;
    
    // Store session in global state
    const sessionState = {
      session_id: sessionId,
      charger: charger,
      merchant: merchant,
      event_id: session.event_id || EVENT_SLUG,
    };
    
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.setItem('pilot_session', JSON.stringify(sessionState));
    }
    
    window.pilotSession = sessionState;
    
    console.log('[Explore] Session started (v1):', session);
    
    // Navigate to Earn page
    navigateToEarn(sessionId, merchantId, chargerId);
    
    hideMerchantPopover();
    
  } catch (e) {
    console.error('[Explore] Failed to start session:', e);
    showToast(`Failed to start session: ${e.message || 'Unknown error'}`);
  }
}

// === Show Discount Code ====================================================
async function showDiscountCode(merchantId, merchantName) {
  // Navigate to show code page using hash route
  location.hash = `#/code?merchant_id=${encodeURIComponent(merchantId)}`;
  
  // Also store merchant name in sessionStorage for the page to access
  if (typeof sessionStorage !== 'undefined') {
    sessionStorage.setItem(`merchant_name_${merchantId}`, merchantName);
  }
}

// === Loading & Empty States ==============================================
function showLoadingState() {
  const scroller = document.getElementById('discover-merchant-scroller');
  if (!scroller) return;
  
  scroller.innerHTML = '<div style="text-align: center; padding: 20px; color: #6B7280; font-size: 14px;">Loading merchants...</div>';
  
  const section = document.getElementById('discover-merchants-section');
  if (section) {
    section.style.display = 'block';
  }
}

function hideLoadingState() {
  // Loading state is cleared when perks are rendered
}

function showEmptyState(message = 'No perks available') {
  // Always show at least Eggman ATX card
  updateRecommendedPerks([]);
}

// === Resy-style Merchant Card Renderer ==================================================
function renderMerchantCard(merchant) {
  const {
    name = 'Merchant',
    rating = 4.6,
    rating_count = 2500,
    category = 'Smoothies',
    price_tier = '$$',
    distance_text = '0.1 mi',
    image_url = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
    logo_url,
    photo_url
  } = merchant;

  // Use photo_url or logo_url as fallback
  const merchantImage = image_url || photo_url || logo_url || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

  const card = document.createElement('div');
  card.className = 'perk-card perk-card--resy';
  card.dataset.merchantId = merchant.id || merchant.merchant_id || '';

  card.innerHTML = `
    <div class="perk-card__left">
      <div class="perk-card__name">${name}</div>
      <div class="perk-card__meta">
        <span class="perk-card__rating">★ ${rating.toFixed(1)}</span>
        <span class="perk-card__rating-count">(${rating_count.toLocaleString()})</span>
        <span class="perk-card__dot">•</span>
        <span class="perk-card__category">${category}</span>
        <span class="perk-card__dot">•</span>
        <span class="perk-card__price">${price_tier}</span>
      </div>
      <div class="perk-card__distance">${distance_text} walk to charger</div>
      <div class="perk-card__nova">Nova accepted here</div>
      <button class="btn btn-primary perk-card__button">View details</button>
    </div>
    <div class="perk-card__right">
      <img src="${merchantImage}" alt="${name}" class="perk-card__image" onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5Y2EzYWYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4='" />
    </div>
  `;

  // Wire up button click
  const button = card.querySelector('.perk-card__button');
  if (button) {
    button.addEventListener('click', (e) => {
      e.stopPropagation();
      openMerchantDetail(merchant);
    });
  }

  // Card click also triggers view details
  card.addEventListener('click', () => {
    openMerchantDetail(merchant);
  });

  return card;
}

// === Discover Subheader (Off-peak Indicator) ======================================
function updateDiscoverSubheader() {
  // Subheader element removed - off-peak indicator is now the charge-chip pill
  // This function kept for compatibility but no longer updates any element
  const el = document.getElementById('discover-subheader');
  if (el) {
    el.textContent = '';
  }
}

// === Discover Merchants Carousel Renderer ===========================================
function renderDiscoverMerchants(merchants) {
  const scroller = document.getElementById('discover-merchant-scroller');
  if (!scroller) return;

  scroller.innerHTML = '';

  // Use the merchants passed in (from search/filter results)
  let allMerchants = [];
  
  if (merchants && merchants.length > 0) {
    // Convert merchant objects to display format
    allMerchants = merchants.map(m => {
      if (m.name && m.category) {
        // Already a merchant object
        return {
          ...m,
          display_name: m.display_name || m.name,
          rating: m.rating || 4.6,
          rating_count: m.rating_count || '2,500',
          price_tier: m.price_tier || '$$',
          distance_text: m.distance_text || (m.walk_time_s ? `${Math.round(m.walk_time_s / 60)} min walk to charger` : '0.1 mi walk to charger'),
          logo_url: m.logo_url || m.image_url || m.photo_url,
        };
      } else {
        // Convert from perk format
        return {
          id: m.id || m.perkId,
          display_name: m.name || 'Merchant',
          name: m.name || 'Merchant',
          rating: 4.6,
          rating_count: '2,500',
          category: m.category || 'Food & Drink',
          price_tier: '$$',
          distance_text: m.walk || '0.1 mi walk to charger',
          logo_url: m.logo || m.logo_url,
        };
      }
    });
  }

  // Render the first merchant from the results (or show empty state)
  const merchant = allMerchants[0];
  if (merchant) {
    // Center map on the first merchant (the one shown in the bottom card)
    // First try to get lat/lng from the merchant object itself
    let merchantLat = merchant.lat;
    let merchantLng = merchant.lng;
    
    // If not available, try to find the merchant in _merchants array by ID/name
    if ((!merchantLat || !merchantLng) && _merchants.length > 0) {
      const fullMerchant = _merchants.find(m => 
        (m.id && merchant.id && m.id === merchant.id) ||
        (m.merchant_id && merchant.merchant_id && m.merchant_id === merchant.merchant_id) ||
        (m.name && merchant.name && m.name === merchant.name) ||
        (m.display_name && merchant.display_name && m.display_name === merchant.display_name)
      );
      if (fullMerchant) {
        merchantLat = fullMerchant.lat;
        merchantLng = fullMerchant.lng;
      }
    }
    
    // Center map if we have coordinates
    if (_map && merchantLat && merchantLng) {
      _map.setView([merchantLat, merchantLng], 15);
      console.log('[Explore] Centered map on merchant card:', merchant.name || merchant.display_name);
    }
    
    const card = document.createElement('article');
    card.className = 'merchant-card';

    const name = merchant.display_name || merchant.name || 'Unknown merchant';
    const distance = merchant.distance_text || '0.1 mi walk to charger';
    const rating = merchant.rating || 4.7;
    const ratingCount = merchant.rating_count || '3,200';
    const category = merchant.category || 'Coffee';
    const priceTier = merchant.price_tier || '$$';
    // Use merchant's logo_url or fallback to a placeholder
    const logoUrl = merchant.logo_url || merchant.image_url || merchant.photo_url || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

    card.innerHTML = `
      <div class="merchant-card__left">
        <div class="merchant-card__name">${name}</div>
        <div class="merchant-card__meta">
          <span class="merchant-card__rating">★ ${rating.toFixed(1)}</span>
          <span class="merchant-card__rating-count">(${ratingCount})</span>
          <span class="merchant-card__dot">•</span>
          <span class="merchant-card__category">${category}</span>
          <span class="merchant-card__dot">•</span>
          <span class="merchant-card__price">${priceTier}</span>
        </div>
        <div class="merchant-card__distance">${distance}</div>
        <div class="merchant-card__nova">Nova accepted here</div>
        <button
          class="btn btn-primary merchant-card__button"
          data-merchant-id="${merchant.id}"
        >
          View details
        </button>
      </div>
      <div class="merchant-card__right">
        <img
          src="${logoUrl}"
          alt="${name}"
          class="merchant-card__image"
          onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5Y2EzYWYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4='"
        />
      </div>
    `;

    scroller.appendChild(card);
    
    // Attach click handler for "View details"
    const btn = card.querySelector('.merchant-card__button');
    if (btn) {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        openMerchantDetail(merchant);
      });
    }
  } else {
    // Show empty state if no merchants
    scroller.innerHTML = '<div style="text-align: center; padding: 40px; color: #6b7280;">No merchants found</div>';
  }

  // Show the section
  const section = document.getElementById('discover-merchants-section');
  if (section) {
    section.style.display = 'block';
  }

  console.log('[Discover][Merchants] Rendered merchant card:', allMerchants[0]?.name || 'none');
}

// === Recommended Perks Management ==================================================
function updateRecommendedPerks(merchants) {
  // Update off-peak indicator
  updateDiscoverSubheader();
  
  // Use new carousel renderer
  renderDiscoverMerchants(merchants);
}

// === Charger Selection =====================================================
async function selectCharger(charger) {
  _selectedChargerId = charger.id;
  
  console.log('Charger tapped:', charger.id, charger.name);
  
  // Center map on charger
  if (_map) {
    _map.setView([charger.lat, charger.lng], 15);
  }
}

// === List View Bottom Sheet ===============================================
function initListViewSheet() {
  const listViewBtn = $('#btn-list-view');
  const mapViewBtn = $('#btn-map-view');
  const sheet = $('#explore-list-sheet');
  
  if (!sheet) return;
  
  // Start collapsed
  sheet.classList.add('collapsed');
  sheet.classList.remove('expanded');
  
  // List View button expands sheet
  if (listViewBtn) {
    listViewBtn.addEventListener('click', () => {
      expandListViewSheet();
    });
  }
  
  // Map View button collapses sheet
  if (mapViewBtn) {
    mapViewBtn.addEventListener('click', () => {
      collapseListViewSheet();
    });
  }
}

function expandListViewSheet() {
  const sheet = $('#explore-list-sheet');
  const listContent = $('#explore-list');
  
  if (!sheet) return;
  
  sheet.classList.remove('collapsed');
  sheet.classList.add('expanded');
  
  // Render merchant cards in list
  if (listContent && _merchants.length > 0) {
    renderMerchantList(_merchants);
  }
}

function collapseListViewSheet() {
  const sheet = $('#explore-list-sheet');
  
  if (!sheet) return;
  
  sheet.classList.remove('expanded');
  sheet.classList.add('collapsed');
}

function renderMerchantList(merchants) {
  const listContent = $('#explore-list');
  if (!listContent) return;
  
  listContent.innerHTML = '';
  
  if (merchants.length === 0) {
    listContent.innerHTML = '<div style="text-align: center; padding: 40px; color: #6b7280;">No merchants found</div>';
    return;
  }
  
  merchants.forEach(merchant => {
    const card = renderMerchantCard(merchant);
    if (card) {
      listContent.appendChild(card);
    }
  });
}

// === Main Initialization ===================================================
export async function initExplore(){
  // Initialize map
  _map = await ensureMap();
  if (_map) {
    setTimeout(() => _map.invalidateSize(), 0);
  }

  await loadPilotData();
  
  // Get user location
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        _userLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        console.log('[Explore] Updated user location', _userLocation);
      },
      () => console.warn('Could not get user location')
    );
  }
  
  // Initialize UI components
  initSearchBar();
  initSuggestions();
  initChargeChip();
  // initMapCenterButton(); // Map center button removed
  
  initMerchantPopover();
  initListViewSheet();
  
  // Listen for redeem_start event from Wallet
  window.addEventListener('nerava:discover:redeem_start', async () => {
    console.log('[Explore] Redeem start event received');
    // Refresh merchants if needed
    if (_merchants.length === 0) {
      await loadPilotData();
    }
    // Auto-select closest merchant and open detail page
    if (_merchants.length > 0) {
      autoSelectClosestMerchant();
    }
  });
  
  // Initialize off-peak indicator
  updateDiscoverSubheader();
  // Update every minute
  setInterval(updateDiscoverSubheader, 60000);

  if (!_merchants.length) {
    showEmptyState('No pilot merchants yet');
  }
  
  // Trigger map resize
  setTimeout(() => {
    if (_map && _map.invalidateSize) {
      _map.invalidateSize();
    }
  }, 100);
}
