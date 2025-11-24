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

import { fetchPilotBootstrap, fetchPilotWhileYouCharge } from '../core/api.js';
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
  return {
    id: merchant.id || merchant.merchant_id || `merchant_${Math.random().toString(36).slice(2)}`,
    name: merchant.name || 'Merchant',
    lat: Number(merchant.lat),
    lng: Number(merchant.lng),
    category: merchant.category || 'other',
    distance_m: normalizeNumber(merchant.distance_m || 0),
    walk_time_s: walkTime,
    nova_reward: normalizeNumber(merchant.nova_reward || merchant.total_nova_awarded || 0),
    logo: merchant.logo_url || merchant.logo || '',
    raw: merchant,
  };
}

function merchantToPerkCard(merchant) {
  const walkMinutes = merchant.walk_time_s
    ? Math.max(1, Math.round(merchant.walk_time_s / 60))
    : merchant.distance_m
    ? `${merchant.distance_m} m walk`
    : 'Walkable';
  return {
    id: merchant.id,
    name: merchant.name,
    logo: merchant.logo || merchant.logo_url || `https://logo.clearbit.com/${merchant.name?.toLowerCase().replace(/\s+/g, '') || 'merchant'}.com`,
    nova: merchant.nova_reward || 0,
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
    _pilotBootstrap = bootstrap || FALLBACK_HUB;
    _pilotMode = _pilotBootstrap?.pilot_mode !== false;
    updateHubHeader(_pilotBootstrap);

    const chargers = (_pilotBootstrap.chargers || [])
      .map(toMapCharger)
      .filter(Boolean);

    if (chargers.length) {
      _chargers = chargers;
      renderChargerPins(chargers);
    } else {
      _chargers = fallbackChargers();
      renderChargerPins(_chargers);
    }

    const whileYouCharge = await fetchPilotWhileYouCharge();
    const merchantsRaw =
      whileYouCharge?.recommended_merchants || whileYouCharge?.merchants || [];
    _merchants = merchantsRaw.map(toMapMerchant).filter(Boolean);

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
  const moreBtn = $('#popover-more-details');
  
  if (startBtn) {
    startBtn.addEventListener('click', () => {
      console.log('Start session clicked');
      // TODO: Implement session start
      showToast('Starting session...');
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
  
  const chargerName = charger?.name || 'charger';
  const perkText = merchant.perk || merchant.blurb || 'Get perks while you charge';
  
  if (logoEl) logoEl.src = merchant.merchant?.logo || merchant.logo || '';
  if (nameEl) nameEl.textContent = merchant.merchant?.name || merchant.name || 'Merchant';
  if (textEl) textEl.textContent = `Get ${perkText} while you charge at ${chargerName}`;
  
  popover.style.display = 'block';
  _selectedMerchantId = merchant.id;
}

function hideMerchantPopover() {
  const popover = $('#merchant-popover');
  if (popover) {
    popover.style.display = 'none';
  }
  _selectedMerchantId = null;
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
  
  const perksToShow = perks.slice(0, 3);
  
  // Clear existing cards
  row.innerHTML = '';
  
  // Render exactly 3 compact perk cards
  perksToShow.forEach(perk => {
    const card = document.createElement('div');
    card.className = 'perk-card-compact';
    card.dataset.perkId = perk.id || '';
    
    // Compact layout: Logo + "Earn X Nova" + "X min walk"
    card.innerHTML = `
      <img class="perk-card-logo" src="${perk.logo || ''}" alt="${perk.name || ''}" onerror="this.src='https://via.placeholder.com/48?text=${encodeURIComponent((perk.name || 'M')[0])}'">
      <div class="perk-card-reward">Earn ${perk.nova || 0} Nova</div>
      <div class="perk-card-walk">${perk.walk || '0 min walk'}</div>
    `;
    
    // Handle card click
    card.addEventListener('click', () => {
      console.log('[WhileYouCharge] Recommended perk clicked:', perk.name);
      // TODO: Show merchant detail or start session
      showMerchantPopover({
        merchant: { name: perk.name, logo: perk.logo },
        perk: `Earn ${perk.nova} Nova`,
        blurb: perk.walk
      });
    });
    
    row.appendChild(card);
  });
  
  // Show container with animation
  container.style.display = 'block';
  container.style.opacity = '0';
  container.classList.add('visible');
  void container.offsetHeight; // Force reflow
  
  console.log(`[WhileYouCharge] Rendered ${perksToShow.length} perk cards`);
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
