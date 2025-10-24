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

// ---------- tabs ----------
const pages = {
  explore: document.getElementById('page-explore'),
  charge:  document.getElementById('page-charge'),
  wallet:  document.getElementById('page-wallet'),
  profile: document.getElementById('page-profile'),
  claim:   document.getElementById('page-claim')
};
const banner = $('#incentive-banner');

function setTab(tab){
  for (const [k,el] of Object.entries(pages)) if (el) el.classList.toggle('active', k===tab);
  document.querySelectorAll('.tabbar .tab').forEach(b=> b.classList.toggle('active', b.dataset.tab===tab));
  if (tab==='charge') initChargePage();
  if (tab==='explore' && typeof window.initExplorePage==='function') window.initExplorePage();
  if (tab === 'explore' && window._map) {
    setTimeout(()=> window._map.invalidateSize(), 60);
    if (window._routeBounds) window._map.fitBounds(window._routeBounds, {maxZoom:16, padding:[20,20]});
  }
}

document.querySelectorAll('.tabbar .tab').forEach(b=> b.onclick = (e) => {
  e.preventDefault();
  const tab = b.dataset.tab;
  if (tab) setTab(tab);
});

// ---------- map ----------
let map;
function ensureMap({lat=30.4021,lng=-97.7265}={}){
  if (map) return map;
  map = L.map('map',{ zoomControl:false, attributionControl:true }).setView([lat,lng], 14);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom: 19, attribution: '&copy; OpenStreetMap'
  }).addTo(map);
  window._map = map;
  return map;
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

// ---------- boot ----------
window.addEventListener('load', async ()=>{
  // Sync --brand from logo color if present (no-op if unchanged)
  try {
    const logo = document.querySelector('.brand-logo .brand-text');
    const root = document.documentElement;
    if (logo && root) {
      const cs = getComputedStyle(logo);
      const color = cs.color;
      if (color) root.style.setProperty('--brand', color);
    }
  } catch {}
  
  // Cleanup scan modal if it somehow exists
  try{ const m=document.getElementById('scanModal'); if(m) m.remove(); }catch(_){}
  
  await loadBanner();
  if (window.location.hash === '#/wallet') setTab('wallet');
  else setTab('explore');
  try{ const mod = await import('./js/pages/explore.js'); await mod.initExplore(); }catch(_){}
  await loadWallet();
  await loadPrefs();
  // keep Leaflet healthy on resize/orientation
  let t; const kick = ()=>{ clearTimeout(t); t=setTimeout(()=>{ try{ map && map.invalidateSize(false); }catch(_){ } }, 120); };
  window.addEventListener('resize', kick, {passive:true});
  window.addEventListener('orientationchange', kick, {passive:true});
});