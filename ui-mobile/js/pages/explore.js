import { apiGet } from '../core/api.js';
import { ensureMap } from '../app.js';
import { setTab } from '../app.js';

const $ = (s, r=document) => r.querySelector(s);

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

// === Explore: Next Charger Micro-State =====================================
const CHARGER_FALLBACK = [
  { id: 'hub_arboretum', name:'Arboretum Supercharger', addr:'9722 Great Hills Trl, Austin, TX', lat:30.3996, lng:-97.7472, merchant:{name:'Starbucks', logo:'https://logo.clearbit.com/starbucks.com'}, perk:'Free coffee 2–4pm • 3 min walk' },
  { id: 'hub_domain',     name:'Domain Northside',      addr:'11821 Rock Rose Ave, Austin, TX', lat:30.4019, lng:-97.7251, merchant:{name:'Neiman Marcus', logo:'https://logo.clearbit.com/neimanmarcus.com'}, perk:'10% off with charge • 4 min walk' },
  { id: 'hub_dt',         name:'Downtown 5th & Lavaca', addr:'500 Lavaca St, Austin, TX',       lat:30.2676, lng:-97.7429, merchant:{name:'Starbucks', logo:'https://logo.clearbit.com/starbucks.com'}, perk:'Free coffee 2–4pm • 3 min walk' }
];

let _chargers = [];     // resolved list (api or fallback)
let _cIdx = 0;          // index in the list

// Help: safe API fetch with null on 404
async function tryGet(url){
  try { return await apiGet(url); } catch(e){ return null; }
}

// Draw currently selected charger into map + perk
async function selectCharger(idx){
  if(!_chargers.length) return;

  _cIdx = (idx + _chargers.length) % _chargers.length;
  const c = _chargers[_cIdx];

  // 1) Update perk card content
  const $t = (sel) => document.querySelector(sel);
  const titleEl = $t('#perk-title');
  const addressEl = $t('#perk-address');
  const subEl = $t('#perk-sub');
  const logo = $t('#perk-logo');
  
  if (titleEl) titleEl.textContent = c.merchant?.name || 'Nearby merchant';
  if (addressEl) addressEl.textContent = c.addr || '';
  if (subEl) subEl.textContent = c.perk || '';
  if (logo && c.merchant?.logo) { 
    logo.src = c.merchant.logo; 
    logo.alt = c.merchant.name; 
  }

  // 2) Update map: charger (c.lat/lng) to merchant (fake offset for demo)
  const charger = { lat: c.lat, lng: c.lng };
  const merchant = { lat: c.lat + 0.0045, lng: c.lng - 0.0030 }; // small offset so route is visible
  if(window.drawWalkingRoute){
    await window.drawWalkingRoute(charger, merchant, { fit: true, maxZoom: 16 });
  }
}

function _bindPerk(deal=_fallbackDeal) {
  const $ = (sel)=>document.querySelector(sel);
  $("#perk-title").textContent   = deal.merchant?.name || "Starbucks";
  $("#perk-address").textContent = deal.merchant?.address || "310 E 5th St, Austin, TX";
  $("#perk-sub").textContent     = deal.blurb || "Free coffee 2–4pm • 3 min walk";

  const logoEl = $("#perk-logo");
  if (logoEl) {
    const primary = deal.merchant?.logo || STARBUCKS_LOGO_LOCAL;
    logoEl.src = primary;

    // Fallback if the primary (local) fails
    logoEl.onerror = () => {
      if (logoEl.dataset.fallback !== "1") {
        logoEl.dataset.fallback = "1";
        logoEl.src = STARBUCKS_LOGO_CDN;
      }
    };
    // Ensure containment styling applies even if external image loads
    logoEl.decoding = "async";
    logoEl.loading = "lazy";
    logoEl.alt = deal.merchant?.name || "Starbucks";
  }

              // Ensure CTA has correct classes and behavior
              const cta = document.getElementById('perk-cta');
              if (cta) {
                cta.classList.add('btn', 'btn-primary', 'btn-wide');
                cta.onclick = () => setTab('charge'); // existing helper
              }
  $("#view-more")?.addEventListener("click", ()=> window.openPerksList?.());
}

export async function initExplore(){
  const map = await ensureMap();          // uses existing map initializer
  setTimeout(() => map.invalidateSize(), 0);

  // resolve chargers from API, then fallback
  const around = await tryGet('/v1/hubs/available');   // OPTIONAL endpoint
  _chargers = Array.isArray(around) && around.length ? around.map(r => ({
    id: r.id, name: r.name, addr: r.address, lat: r.lat, lng: r.lng,
    merchant: r.merchant || { name: 'Starbucks', logo: 'https://logo.clearbit.com/starbucks.com' },
    perk: r.perk || 'Free coffee 2–4pm • 3 min walk'
  })) : CHARGER_FALLBACK.slice();

  // initial selection
  await selectCharger(0);

  // wire next button
  const nextBtn = document.getElementById('next-charger-btn');
  if(nextBtn && !nextBtn._wired){
    nextBtn._wired = true;
    nextBtn.addEventListener('click', async ()=>{
      await selectCharger(_cIdx + 1);
      // small haptic-like feedback
      nextBtn.animate([{transform:'scale(1)'},{transform:'scale(0.97)'},{transform:'scale(1)'}],{duration:120});
    });
  }

  // Fit to any existing route bounds if available; otherwise default city view
  if (window.lastBounds){
    map.fitBounds(window.lastBounds, { padding:[20,20] });
  } else {
    map.setView([30.2672, -97.7431], 14);
  }

  // Populate perk card with API data or fallback
  try {
    const [hub, deals] = await Promise.all([
      apiGet("/v1/hubs/recommend").catch(()=>null),
      apiGet("/v1/deals/nearby").catch(()=>null)
    ]);
    const deal = deals?.[0] || _fallbackDeal;
    _bindPerk(deal);
  } catch {
    _bindPerk(_fallbackDeal);
  }

  // Make sure the map card never overlaps content
  const card = $('.map-card');
  if (card){ card.style.zIndex = 0; }
}