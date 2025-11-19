/**
 * Explore Page - Apple Maps-style redesign
 * 
 * FILE STRUCTURE:
 * - HTML: ui-mobile/index.html (lines 84-179: #page-explore section)
 * - JS: ui-mobile/js/pages/explore.js (this file)
 * - Map Core: ui-mobile/js/core/map.js (Leaflet-based map utilities)
 * 
 * DATA SOURCES:
 * - Chargers: /v1/hubs/nearby or /v1/hubs/recommend (fallback to CHARGER_FALLBACK)
 * - Merchants/Perks: /v1/deals/nearby (fallback to _fallbackDeal)
 * - User location: navigator.geolocation API
 * 
 * NEW STRUCTURE (Apple Maps-style):
 * - Full-screen map background
 * - Top overlay: SearchBar + SuggestionsRow
 * - Right-side controls: Locate me + Filters
 * - AirDrop-style popover: Merchant quick view on tap (shown on charger/merchant tap)
 */

import { apiGet } from '../core/api.js';
import { ensureMap, clearStations, addStationDot, fitToStations, getMap } from '../core/map.js';
import { setTab } from '../app.js';

const $ = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));

// Prefer local asset; will fallback to Clearbit if it fails to load.
const STARBUCKS_LOGO_LOCAL = "./img/brands/starbucks.png";
const STARBUCKS_LOGO_CDN   = "https://logo.clearbit.com/starbucks.com";

const _fallbackDeal = {
  merchant: {
    name: "Starbucks",
    address: "310 E 5th St, Austin, TX",
    logo: STARBUCKS_LOGO_LOCAL
  },
  blurb: "Free coffee 2–4pm • 3 min walk"
};

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

// === State Management ======================================================
let _chargers = [];
let _merchants = [];
let _selectedChargerId = null;
let _selectedMerchantId = null;
let _selectedCategory = null;
let _userLocation = null;
let _map = null;

// Help: safe API fetch with null on 404 (silent for expected failures)
async function tryGet(url){
  try { 
    return await apiGet(url); 
  } catch(e){ 
    if (e.message && e.message.includes('404')) {
      return null;
    }
    console.warn(`API call failed for ${url}:`, e.message);
    return null; 
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
function initSearchBar() {
  const searchInput = $('#explore-search-input');
  const voiceBtn = $('#explore-voice-btn');
  
  if (!searchInput) return;
  
  // Text search (TODO: wire to actual search API)
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    if (query.length > 0) {
      console.log('Search query:', query);
      // TODO: Filter merchants/chargers by query
      // For now, just log
    }
  });
  
  // Voice search (TODO: implement voice recognition)
  if (voiceBtn) {
    voiceBtn.addEventListener('click', () => {
      console.log('Voice search clicked');
      // TODO: Implement voice search
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

function filterByCategory(category) {
  console.log('Filtering by category:', category);
  // TODO: Implement actual filtering logic
  // For now, just log the filter selection
  // Future: Filter charger markers or merchant popovers based on category
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

// === Recommended Perks Management ==================================================
// Single container card with 3 compact perks side-by-side
function renderRecommendedPerks(perks) {
  const container = $('#recommended-perks-container');
  const row = $('#recommended-perks-row');
  
  if (!container || !row) return;
  
  // Use provided perks or default recommended perks (exactly 3)
  const perksToShow = (perks && perks.length > 0 ? perks : _recommendedPerks).slice(0, 3);
  
  // Hide if no perks
  if (perksToShow.length === 0) {
    container.style.display = 'none';
    container.classList.remove('visible');
    return;
  }
  
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
      console.log('Recommended perk clicked:', perk.name);
      // TODO: Show merchant detail or start session
      showMerchantPopover({
        merchant: { name: perk.name, logo: perk.logo },
        perk: `Earn ${perk.nova} Nova`,
        blurb: perk.walk
      });
    });
    
    row.appendChild(card);
  });
  
  // Show with animation
  container.style.display = 'block';
  container.style.opacity = '0'; // Reset for animation
  // Trigger animation on next frame
  requestAnimationFrame(() => {
    container.classList.add('visible');
    // Force reflow to ensure animation triggers
    void container.offsetHeight;
  });
}

function updateRecommendedPerks(perks) {
  // Use provided perks or default recommended perks
  const perksToShow = perks && perks.length > 0 ? perks : _recommendedPerks;
  renderRecommendedPerks(perksToShow);
}

// === Charger Selection =====================================================
function selectCharger(charger) {
  _selectedChargerId = charger.id;
  
  console.log('Charger tapped:', charger.id, charger.name);
  
  // Center map on charger
  if (_map) {
    _map.setView([charger.lat, charger.lng], 15);
  }
  
  // Update perk rail with merchants for this charger
  // For now, use dummy merchants; later replace with API call
  updateRecommendedPerks(_recommendedPerks);
  
  // TODO: Show merchant popover or overlay when charger is tapped
  // For now, just log the selection
}

// === Main Initialization ===================================================
export async function initExplore(){
  // Initialize map
  _map = await ensureMap();
  if (_map) {
    setTimeout(() => _map.invalidateSize(), 0);
  }

  // Load chargers
  clearStations();
  let stations = [];
  
  try {
    const data = await apiGet('/v1/hubs/nearby');
    if (data?.stations?.length) {
      stations = data.stations;
      console.log(`Loaded ${stations.length} stations from API`);
    }
  } catch (e) {
    console.warn('Failed to load stations:', e);
  }
  
  // Fallback to single charger if API fails
  if (stations.length === 0) {
    const rec = await tryGet('/v1/hubs/recommend');
    if (rec) {
      stations = [{
        id: 'hub_recommended',
        name: `${rec.network?.name || 'Tesla'} Supercharger`,
        lat: Number(rec.dest?.lat || 30.401),
        lng: Number(rec.dest?.lng || -97.725),
        network: rec.network?.name || 'Tesla',
        eta_min: rec.eta_min || 15
      }];
    } else {
      stations = CHARGER_FALLBACK.slice(0, 3).map(c => ({
        id: c.id,
        name: c.name,
        lat: c.lat,
        lng: c.lng,
        network: 'Tesla',
        eta_min: 15
      }));
    }
  }
  
  // Add charger markers to map with branded pins
  for (const st of stations) {
    await addStationDot(st, {
      onClick: (station) => {
        selectCharger(station);
      }
    });
  }
  
  // Update state
  _chargers = stations.map(st => ({
    id: st.id,
    name: st.name,
    lat: st.lat,
    lng: st.lng,
    merchant: { name: 'Starbucks', logo: 'https://logo.clearbit.com/starbucks.com' },
    perk: 'Free coffee 2–4pm • 3 min walk',
    eta_min: st.eta_min || 15
  }));
  
  // Load merchants/perks
  try {
    const perk = await apiGet("/v1/deals/nearby");
    if (perk) {
      _merchants = [{
        id: perk.id || 'perk_1',
        merchant: {
          name: perk.merchant || 'Starbucks',
          address: perk.address || '310 E 5th St, Austin, TX',
          logo: perk.logo || 'https://logo.clearbit.com/starbucks.com'
        },
        perk: `${perk.window_text || 'Free coffee 2–4pm'} • ${perk.distance_text || '3 min walk'}`,
        blurb: `${perk.window_text || 'Free coffee 2–4pm'} • ${perk.distance_text || '3 min walk'}`
      }];
    } else {
      _merchants = [_fallbackDeal];
    }
  } catch {
    _merchants = [_fallbackDeal];
  }
  
  // Auto-select first charger
  if (stations.length > 0) {
    selectCharger(stations[0]);
  }
  
  // Fit map to show all stations
  fitToStations(stations);
  
  // Default view if no stations
  if (stations.length === 0 && _map) {
    _map.setView([30.2672, -97.7431], 14);
  }
  
  // Get user location
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        _userLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        // Optionally center map on user
        // if (_map) _map.setView([_userLocation.lat, _userLocation.lng], 14);
      },
      () => console.warn('Could not get user location')
    );
  }
  
  // Initialize UI components
  initSearchBar();
  initSuggestions();
  initMerchantPopover();
  
  // Initialize perk rail with dummy merchants
  updateRecommendedPerks(_recommendedPerks);
  
  // Trigger map resize
  setTimeout(() => {
    if (_map && _map.invalidateSize) {
      _map.invalidateSize();
    }
  }, 100);
}
