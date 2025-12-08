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
} from '../core/api.js';
import { ensureMap, clearStations, addStationDot, fitToStations, getMap } from '../core/map.js';
import { setTab } from '../app.js';
import { getOptimalChargingTime, getChargingStateDisplay, getChargingState } from '../core/charging-state.js';

// Leaflet reference (assumes L is global from Leaflet script)
const L = window.L;

const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));

// Prefer local asset; will fallback to Clearbit if it fails to load.
const STARBUCKS_LOGO_LOCAL = "./img/brands/starbucks.png";
const STARBUCKS_LOGO_CDN   = "https://logo.clearbit.com/starbucks.com";

// === Recommended Perks Data =====================================
// Three perks: Starbucks, Target, Whole Foods
const _recommendedPerks = [
  {
    id: 'perk_1',
    name: "Starbucks",
    logo: "https://logo.clearbit.com/starbucks.com",
    nova: 12,
    walk: "3 min walk"
  },
  {
    id: 'perk_2',
    name: "Target",
    logo: "https://logo.clearbit.com/target.com",
    nova: 8,
    walk: "5 min walk"
  },
  {
    id: 'perk_3',
    name: "Whole Foods",
    logo: "https://logo.clearbit.com/wholefoodsmarket.com",
    nova: 10,
    walk: "7 min walk"
  }
];

// === Explore: Next Charger Micro-State =====================================
const CHARGER_FALLBACK = [
  { id: 'hub_arboretum', name:'Arboretum Supercharger', addr:'9722 Great Hills Trl, Austin, TX', lat:30.3996, lng:-97.7472, merchant:{name:'Starbucks', logo:'https://logo.clearbit.com/starbucks.com'}, perk:'Free coffee 2–4pm • 3 min walk' },
  { id: 'hub_domain',     name:'Domain Northside',      addr:'11821 Rock Rose Ave, Austin, TX', lat:30.4019, lng:-97.7251, merchant:{name:'Neiman Marcus', logo:'https://logo.clearbit.com/neimanmarcus.com'}, perk:'10% off with charge • 4 min walk' },
  { id: 'hub_dt',         name:'Downtown 5th & Lavaca', addr:'500 Lavaca St, Austin, TX',       lat:30.2676, lng:-97.7429, merchant:{name:'Starbucks', logo:'https://logo.clearbit.com/starbucks.com'}, perk:'Free coffee 2–4pm • 3 min walk' }
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
  if (!merchant) return null;
  const walkTime = normalizeNumber(merchant.walk_time_s || merchant.walk_seconds || 0);
  
  // Preserve logo_url from API response (could be null, empty, or a URL)
  const logoUrl = merchant.logo_url || merchant.logo || null;
  
  return {
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

// === State Management ======================================================
let _chargers = [];
let _merchants = [];
let _selectedChargerId = null;
let _selectedMerchantId = null;
let _selectedMerchant = null; // Store full merchant object
let _selectedCharger = null; // Store selected charger object
let _selectedCategory = null;
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

async function loadPilotData() {
  showLoadingState();
  try {
    // Get user location for nearby merchants query
    let userLat = 30.4021; // Domain default
    let userLng = -97.7266;
    
    if (_userLocation) {
      userLat = _userLocation.lat;
      userLng = _userLocation.lng;
    }
    
    // Load chargers - use fallback for now (can be migrated to v1 endpoint later)
    _chargers = fallbackChargers();
    renderChargerPins(_chargers);
    
    // Load nearby merchants using v1 API
    console.log('[Explore] Fetching nearby merchants (v1)...');
    let merchantsRaw;
    try {
      const merchantsRes = await apiNearbyMerchants({
        zoneSlug: ZONE_SLUG,
        lat: userLat,
        lng: userLng,
      });
      console.log('[Explore] Nearby merchants (v1) response:', merchantsRes);
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
    console.log('[Explore] Mapped merchants:', _merchants.length, 'merchants');
    
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
    
    // Sort merchants by nova_reward descending (Bakery Lorraine with 2 Nova should appear at top)
    _merchants.sort((a, b) => (b.nova_reward || 0) - (a.nova_reward || 0));

    if (_merchants.length) {
      applyMerchantFilter('');
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

    if (_chargers.length) {
      selectCharger(_chargers[0]);
    }
  } catch (err) {
    console.error('[Explore] Failed to load merchants (v1):', err);
    _chargers = fallbackChargers();
    renderChargerPins(_chargers);
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

    if (_chargers.length) {
      selectCharger(_chargers[0]);
    }
  }
}

function filterMerchants(list, query, category) {
  const needle = (query || '').trim().toLowerCase();
  return list.filter((m) => {
    const categoryMatch = category ? (m.category || '').toLowerCase() === category : true;
    if (!categoryMatch) return false;
    if (!needle) return true;
    return (m.name || '').toLowerCase().includes(needle);
  });
}

function applyMerchantFilter(query = '') {
  _activeQuery = query;
  if (!_merchants.length) {
    showEmptyState('No pilot merchants yet');
    return;
  }
  const filtered = filterMerchants(_merchants, query, _selectedCategory);
  if (!filtered.length) {
    showEmptyState('No matching merchants');
    return;
  }
  // Convert merchants to format expected by Resy-style cards
  const merchantCards = filtered.map(m => ({
    ...m,
    rating: m.rating || 4.6,
    rating_count: m.rating_count || 2500,
    price_tier: m.price_tier || '$$',
    distance_text: m.distance_text || (m.walk_time_s ? `${Math.round(m.walk_time_s / 60)} min` : '0.1 mi'),
    image_url: m.image_url || m.photo_url || m.logo_url,
  }));
  updateRecommendedPerks(merchantCards);
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
    
    // If empty, reset to default "coffee" search
    if (query.length === 0) {
      applyMerchantFilter('');
      return;
    }
    
    // Debounce: wait 500ms after user stops typing
    _searchTimeout = setTimeout(async () => {
      console.log(`[WhileYouCharge] Filtering merchants by query: "${query}"`);
      applyMerchantFilter(query);
    }, 500);
  });
  
  // Enter key triggers immediate search
  searchInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (_searchTimeout) {
        clearTimeout(_searchTimeout);
      }
      
      const query = searchInput.value.trim();
      applyMerchantFilter(query);
    }
  });
  
  // Voice search (TODO: implement voice recognition)
  if (voiceBtn) {
    voiceBtn.addEventListener('click', () => {
      console.log('[WhileYouCharge] Voice search clicked');
      showToast('Voice search coming soon');
    });
  }
}

// === Suggestions Chips =====================================================
function initSuggestions() {
  const chips = $$('.suggestion-chip');
  
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      // Toggle active state
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      
      const category = chip.dataset.category;
      _selectedCategory = category === _selectedCategory ? null : category;
      
      if (!_selectedCategory) {
        chip.classList.remove('active');
      }
      
      // Filter merchants/chargers
      filterByCategory(_selectedCategory);
    });
  });
}

async function filterByCategory(category) {
  console.log('Filtering by category:', category);
  
  const categoryMap = {
    'coffee': 'coffee',
    'food': 'food',
    'groceries': 'groceries',
    'gym': 'gym'
  };
  _selectedCategory = categoryMap[category] || category || null;
  applyMerchantFilter(_activeQuery);
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

function initMapCenterButton() {
  const btn = $('#map-center-btn');
  if (!btn) return;

  btn.addEventListener('click', centerMapOnUser);
  console.log('[Explore] Center map button initialized');
}

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
  // Always show at least JuiceLand card
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
    image_url = './img/placeholder-merchant.jpg',
    logo_url,
    photo_url
  } = merchant;

  // Use photo_url or logo_url as fallback
  const merchantImage = image_url || photo_url || logo_url || './img/placeholder-merchant.jpg';

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
      <img src="${merchantImage}" alt="${name}" class="perk-card__image" onerror="this.src='./img/placeholder-merchant.jpg'" />
    </div>
  `;

  // Wire up button click
  const button = card.querySelector('.perk-card__button');
  if (button) {
    button.addEventListener('click', (e) => {
      e.stopPropagation();
      handlePerkCardStartSession(merchant);
    });
  }

  // Card click also triggers view details
  card.addEventListener('click', () => {
    handlePerkCardStartSession(merchant);
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

  // Create JuiceLand @ Domain card as first (featured)
  const juicelandMerchant = {
    id: 'merchant_juiceland_domain',
    display_name: 'JuiceLand – The Domain',
    name: 'JuiceLand – The Domain',
    rating: 4.7,
    rating_count: '3,200',
    category: 'Smoothies',
    price_tier: '$$',
    distance_text: '0.1 mi walk to charger',
    image_url: 'https://logo.clearbit.com/juiceland.com',
    logo_url: 'https://logo.clearbit.com/juiceland.com',
    lat: 30.4021,
    lng: -97.7266,
  };

  // Combine JuiceLand with other merchants
  const allMerchants = [juicelandMerchant];
  
  if (merchants && merchants.length > 0) {
    // Convert perk objects to merchant objects if needed
    const merchantList = merchants.map(m => {
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
    
    allMerchants.push(...merchantList);
  }

  // Render all merchants
  allMerchants.forEach((merchant) => {
    const card = document.createElement('article');
    card.className = 'merchant-card';

    const name = merchant.display_name || merchant.name || 'Unknown merchant';
    const distance = merchant.distance_text || '0.1 mi walk to charger';
    const rating = merchant.rating || 4.7;
    const ratingCount = merchant.rating_count || '3,200';
    const category = merchant.category || 'Smoothies';
    const priceTier = merchant.price_tier || '$$';
    const logoUrl = merchant.logo_url || merchant.image_url || './img/juiceland-logo.png';

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
          onerror="this.src='./img/placeholder-merchant.jpg'"
        />
      </div>
    `;

    scroller.appendChild(card);
  });

  // Attach click handlers for "View details"
  scroller.querySelectorAll('.merchant-card__button').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const merchantId = e.currentTarget.getAttribute('data-merchant-id');
      if (!merchantId) return;
      // Reuse existing view-merchant logic
      const merchant = allMerchants.find(m => m.id === merchantId);
      if (merchant) {
        handlePerkCardStartSession(merchant);
      }
    });
  });

  // Show the section
  const section = document.getElementById('discover-merchants-section');
  if (section) {
    section.style.display = 'block';
  }

  console.log('[Discover][Merchants] Rendered horizontal carousel with', allMerchants.length, 'merchants');
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
  initMapCenterButton();
  
  initMerchantPopover();
  
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
