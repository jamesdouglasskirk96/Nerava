/* globals L */
import { initChargePage } from './js/pages/charge.js'; // fixed: file now exports it

const BASE = localStorage.NERAVA_URL || location.origin;
const USER = localStorage.NERAVA_USER || "demo@nerava.app";

// ---------- helpers ----------
const $ = sel => document.querySelector(sel);
const show = el => el.classList.remove('hidden');
const hide = el => el.classList.add('hidden');
const fmtMoney = cents => `+$${(Number(cents||0)/100).toFixed(2)}`;
const stripHubIds = s => (s||'').replace(/\bhub_[a-z0-9]+_[a-z0-9]+\b/gi,'').replace(/\s{2,}/g,' ').trim();

const pages = { 
  explore: $('#page-explore'), 
  charge: $('#page-charge'), 
  wallet: $('#page-wallet'), 
  profile: $('#page-profile'), 
  earn: $('#page-claim') 
};
const banner = $('#incentive-banner');

export function setTab(tab){
  Object.entries(pages).forEach(([k,el])=>{
    el?.classList.toggle('active', k===tab);
  });
  document.querySelectorAll('.tabbar .tab').forEach(b=>{
    b.classList.toggle('active', b.dataset.tab===tab);
  });
  if (tab==='explore' && window.ensureMap) { try{ const m=window.ensureMap(); setTimeout(()=>m.invalidateSize(), 100);}catch{} }
}

// Make setTab available globally
window.setTab = setTab;

document.querySelectorAll('.tabbar .tab').forEach(b=> b.addEventListener('click',()=> setTab(b.dataset.tab)));
document.querySelector('.earn-pill')?.addEventListener('click', ()=> setTab('earn'));

let map;
export function ensureMap(lat = 30.4021, lng = -97.7265, zoom = 15) {
  // reuse existing map instance if present
  if (window._neravaMap) {
    try { window._neravaMap.invalidateSize(); } catch(_) {}
    return window._neravaMap;
  }

  const el = document.getElementById('map');
  if (!el || !window.L) return null;

  const m = L.map(el, { zoomControl: false }).setView([lat, lng], zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(m);

  // 🔒 hide Leaflet attribution permanently
  const hideAttribution = () => {
    const ctrl = document.querySelector('.leaflet-control-attribution');
    const wrapper = document.querySelector('.leaflet-bottom.leaflet-right');
    if (ctrl) ctrl.style.display = 'none';
    if (wrapper) wrapper.style.display = 'none';
  };
  setTimeout(hideAttribution, 250);
  m.on('load', hideAttribution);

  window._neravaMap = m;
  // expose once for any legacy code
  window.map = m;
  return m;
}

// Draw route + markers + ETA (foot). Fallback to straight line if OSRM blocked.
async function drawWalkingRoute(charger, merchant, logo='☕️'){
  const m = ensureMap({lat:charger.lat, lng:charger.lng});
  // clear previous layer group
  if (window._routeLayer) { window._routeLayer.remove(); window._routeLayer = null; }
  const g = L.layerGroup().addTo(m);
  window._routeLayer = g;

  const chargerIcon = L.divIcon({className:'', html:'<div style="width:12px;height:12px;background:#0ea5e9;border-radius:50%;box-shadow:0 0 0 3px rgba(14,165,233,.25)"></div>'});
  const merchIcon = L.divIcon({className:'', html:`<div style="width:40px;height:40px;border-radius:12px;background:#fff;display:grid;place-items:center;box-shadow:0 8px 24px rgba(16,24,40,.2);font-size:22px">${logo}</div>`});
  const a = L.marker([charger.lat, charger.lng], {icon:chargerIcon}).addTo(g);
  const b = L.marker([merchant.lat, merchant.lng], {icon:merchIcon}).addTo(g);

  // optimistic straight line (visible quickly)
  const straight = L.polyline([[charger.lat,charger.lng],[merchant.lat,merchant.lng]], {color:'#0b57d0', weight:4, opacity:.35, dashArray:'6 8'}).addTo(g);

  let seconds = null, coords = null;
  try{
    const url = `https://router.project-osrm.org/route/v1/foot/${charger.lng},${charger.lat};${merchant.lng},${merchant.lat}?overview=full&geometries=geojson`;
    const r = await fetch(url, {mode:'cors'});
    if (r.ok){
      const j = await r.json();
      const route = j?.routes?.[0];
      seconds = Math.round(route.duration);
      coords = route.geometry.coordinates.map(([x,y])=>[y,x]);
    }
  }catch(_){}
  if (coords){
    straight.remove();
    L.polyline(coords, {color:'#0b57d0', weight:5, opacity:.85}).addTo(g);
  }
  // fit bounds
  const bounds = L.latLngBounds([[charger.lat,charger.lng],[merchant.lat,merchant.lng]]);
  m.fitBounds(bounds, {maxZoom:16, padding:[20,20]});
  window._routeBounds = bounds;

  // ETA badge
  const mins = seconds ? Math.max(1, Math.round(seconds/60)) : Math.max(1, Math.round(bounds.getSouthWest().distanceTo(bounds.getNorthEast())/100)/10);
  const eta = document.getElementById('etaText'); const badge = document.getElementById('routeBadge');
  if (eta && badge){ eta.textContent = `${mins} min walk`; badge.classList.remove('hidden'); }
}
window.drawWalkingRoute = drawWalkingRoute;

// ---------- wallet ----------
async function loadWallet(){
  try{
    const r = await fetch(`${BASE}/v1/social/pool`);
    const j = await r.json();
    $('#wallet-earnings').textContent = fmtMoney(j.total_cents || 0);
  }catch(_){}
}

// ---------- banner ----------
async function loadBanner(){
  try{
    const r = await fetch(`${BASE}/v1/incentives/banner`);
    const j = await r.json();
    if(j?.text){
      $('#banner-text').textContent = j.text;
      show(banner);
    }
  }catch(_){}
}

// ---------- preferences ----------
async function loadPrefs(){
  try{
    const r = await fetch(`${BASE}/v1/user/preferences`);
    const j = await r.json();
    $('#pref-notifications').checked = j?.notifications ?? true;
    $('#pref-location').checked = j?.location ?? true;
  }catch(_){}
}

async function savePrefs(){
  try{
    await fetch(`${BASE}/v1/user/preferences`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        notifications: $('#pref-notifications').checked,
        location: $('#pref-location').checked
      })
    });
    alert('Preferences saved.');
  }catch{ alert('Failed to save preferences'); }
}

$('#btn-save-prefs').addEventListener('click', savePrefs);
$('#btn-see-new').addEventListener('click', ()=>{ setTab('explore'); });

// hard-kill any lingering scan modal nodes (legacy)
document.querySelectorAll('#scanModal, dialog[aria-label="Scan a charger"]').forEach(n=>n.remove());

// ---------- boot ----------
window.addEventListener('load', async ()=>{
  setTab('explore');
  ensureMap();
  await loadBanner();
  // explore.js will draw perk and route on its own
  await loadWallet();
  await loadPrefs();
});