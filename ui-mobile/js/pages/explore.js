/**
 * Explore Page - Apple Maps-style redesign
 * 
 * FILE STRUCTURE:
 * - HTML: ui-mobile/index.html (lines 84-179: #page-explore section)
 * - JS: ui-mobile/js/pages/explore.js (this file)
 * - Map Core: ui-mobile/js/core/map.js (Leaflet-based map utilities)
 * 
 * DATA SOURCES:
 * - Pilot Bootstrap: /v1/pilot/app/bootstrap (fallback to CHARGER_FALLBACK)
 * - Merchants/Perks: /v1/pilot/while_you_charge (fallback to _recommendedPerks)
 * - User location: navigator.geolocation API
 * 
 * NEW STRUCTURE (Apple Maps-style):
 * - Full-screen map background
 * - Top overlay: SearchBar + SuggestionsRow
 * - Right-side controls: Locate me + Filters
 * - AirDrop-style popover: Merchant quick view on tap (shown on charger/merchant tap)
 */

import Api, { fetchPilotBootstrap, fetchPilotWhileYouCharge } from '../core/api.js';
import { ensureMap, clearStations, addStationDot, fitToStations, getMap } from '../core/map.js';
import { setTab } from '../app.js';

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
  fitToStations(chargers);
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

function updateHubHeader(bootstrap) {
  const title = document.querySelector('.recommended-perks-title');
  if (title && bootstrap?.hub_name) {
    title.textContent = `${bootstrap.hub_name} merchants`;
  }
}

async function loadPilotData() {
  showLoadingState();
  try {
    const bootstrap = await fetchPilotBootstrap();
    console.log('[Explore] Bootstrap response:', bootstrap);
    _pilotBootstrap = bootstrap || FALLBACK_HUB;
    _pilotMode = _pilotBootstrap?.pilot_mode !== false;
    
    console.log('[Explore] Pilot mode:', _pilotMode, 'Hub:', _pilotBootstrap?.hub_name || _pilotBootstrap?.hub_id);
    updateHubHeader(_pilotBootstrap);

    const chargers = (_pilotBootstrap.chargers || [])
      .map(toMapCharger)
      .filter(Boolean);
    
    console.log('[Explore] Loaded chargers from bootstrap:', chargers.length, chargers);

    if (chargers.length) {
      _chargers = chargers;
      renderChargerPins(chargers);
    } else {
      _chargers = fallbackChargers();
      renderChargerPins(_chargers);
    }

    console.log('[Explore] About to fetch while_you_charge...');
    let whileYouCharge;
    try {
      whileYouCharge = await fetchPilotWhileYouCharge();
      console.log('[Explore] While you charge response:', whileYouCharge);
    } catch (err) {
      console.error('[Explore] Error fetching while_you_charge:', err);
      throw err; // Re-throw to be caught by outer catch
    }
    
    const merchantsRaw = whileYouCharge?.recommended_merchants || [];
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
      showEmptyState('No pilot merchants yet');
    }

    if (_chargers.length) {
      selectCharger(_chargers[0]);
    }
  } catch (err) {
    console.error('[Explore] Pilot data error:', err);
    _pilotBootstrap = FALLBACK_HUB;
    _chargers = fallbackChargers();
    renderChargerPins(_chargers);
    _merchants = [];
    updateRecommendedPerks(_recommendedPerks);
    showEmptyState('Pilot data unavailable – please try again.');

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
  updateRecommendedPerks(filtered.map(merchantToPerkCard));
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
  
  if (moreBtn) {
    moreBtn.addEventListener('click', () => {
      console.log('More details clicked');
      // TODO: Navigate to merchant detail page
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

// === Start Session Handler ==================================================
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
    // Call pilot API to start session
    const sessionData = await Api.pilotStartSession(
      userLat,
      userLng,
      chargerId,
      merchantId,
      123 // TODO: Get actual user_id from auth state
    );
    
    // Store session in global state (sessionStorage for persistence)
    const sessionState = {
      session_id: sessionData.session_id,
      charger: sessionData.charger || charger,
      merchant: sessionData.merchant || merchant,
      hub_id: sessionData.hub_id,
      hub_name: sessionData.hub_name
    };
    
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.setItem('pilot_session', JSON.stringify(sessionState));
    }
    
    // Also store in window for immediate access
    window.pilotSession = sessionState;
    
    console.log('[Explore] Session started:', sessionData.session_id);
    
    // Navigate to Earn page with all necessary params
    location.hash = `#/earn?session_id=${encodeURIComponent(sessionData.session_id)}&merchant_id=${encodeURIComponent(merchantId)}&charger_id=${encodeURIComponent(chargerId)}`;
    
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
  const container = $('#recommended-perks-container');
  if (!container) return;
  
  const row = container.querySelector('.recommended-perks-row');
  if (!row) return;
  
  row.innerHTML = '<div style="text-align: center; padding: 20px; color: #6B7280; font-size: 14px;">Loading perks...</div>';
  container.style.display = 'block';
  container.classList.add('visible');
}

function hideLoadingState() {
  // Loading state is cleared when perks are rendered
}

function showEmptyState(message = 'No perks available') {
  const container = $('#recommended-perks-container');
  if (!container) return;
  
  const row = container.querySelector('.recommended-perks-row');
  if (!row) return;
  
  row.innerHTML = `<div style="text-align: center; padding: 20px; color: #6B7280; font-size: 14px;">${message}</div>`;
  container.style.display = 'block';
  container.classList.add('visible');
}

// === Recommended Perks Management ==================================================
function updateRecommendedPerks(perks) {
  const container = $('#recommended-perks-container');
  const row = container?.querySelector('.recommended-perks-row');
  
  if (!container || !row) return;
  
  // Hide if no perks
  if (!perks || perks.length === 0) {
    showEmptyState('No perks found');
    return;
  }
  
  // Sort perks by nova_reward descending (already sorted, but ensure)
  const sortedPerks = [...perks].sort((a, b) => (b.nova || b.nova_reward || 0) - (a.nova || a.nova_reward || 0));
  
  // Clear existing cards
  row.innerHTML = '';
  // Horizontal scrolling is handled by CSS, no need for overflow styles here
  
  // Render all perk cards in scrollable list
  sortedPerks.forEach((perk, index) => {
    const card = document.createElement('div');
    card.className = 'perk-card-compact';
    card.dataset.perkId = perk.id || '';
    
    // Debug first perk logo
    if (index === 0) {
      console.log('[Explore] === FIRST PERK CARD DEBUG ===');
      console.log('[Explore] Perk name:', perk.name);
      console.log('[Explore] Perk logo value:', perk.logo);
      console.log('[Explore] Perk logo type:', typeof perk.logo);
      console.log('[Explore] Perk logo truthy?', !!perk.logo);
      console.log('[Explore] Perk logo trimmed?', perk.logo && perk.logo.trim());
      console.log('[Explore] === END FIRST PERK CARD DEBUG ===');
    }
    
          // Compact layout: Logo (only if exists) + "Earn X Nova" + "X min walk"
          const logoHtml = (perk.logo && perk.logo.trim() && perk.logo !== 'null') 
            ? `<img class="perk-card-logo" src="${perk.logo}" alt="${perk.name || ''}" onerror="this.classList.add('hidden')">`
            : '';
    
    card.innerHTML = `
      ${logoHtml}
      <div class="perk-card-reward">Earn ${perk.nova || 0} Nova</div>
      <div class="perk-card-walk">${perk.walk || '0 min walk'}</div>
    `;
    
    // Handle card click
    card.addEventListener('click', () => {
      console.log('[WhileYouCharge] Recommended perk clicked:', perk.name);
      // Find the full merchant object from _merchants
      const fullMerchant = _merchants.find(m => m.id === perk.id);
      // Get current selected charger or default to first
      let currentCharger = null;
      if (_selectedChargerId) {
        currentCharger = _chargers.find(c => c.id === _selectedChargerId);
      }
      if (!currentCharger && _chargers.length > 0) {
        currentCharger = _chargers[0];
      }
      showMerchantPopover(fullMerchant || perk, currentCharger);
    });
    
    row.appendChild(card);
  });
  
  // Show container with animation
  container.style.display = 'block';
  container.style.opacity = '0';
  container.classList.add('visible');
  void container.offsetHeight; // Force reflow
  
  console.log(`[WhileYouCharge] Rendered ${sortedPerks.length} perk cards`);
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
  
  initMerchantPopover();

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
