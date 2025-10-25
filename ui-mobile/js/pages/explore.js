import { apiGet } from '../core/api.js';
// ensureMap should already exist in app.js; if not, create a local fallback
const getMap = (center=[30.4025,-97.7258], zoom=14) => {
  if (window.ensureMap) return window.ensureMap(center[0], center[1], zoom);
  // Minimal local init fallback (won't duplicate)
  if (!window._map) {
    window._map = L.map('map', { zoomControl:false }).setView(center, zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{ maxZoom:19 }).addTo(window._map);
  }
  return window._map;
};

export async function initExplore(){
  // 1) Data (with graceful fallbacks)
  let hub = null, deal = null;
  try { hub = await apiGet('/v1/hubs/recommend'); } catch {}
  try { deal = await apiGet('/v1/deals/nearby'); } catch {}
  if (!hub) hub = { lat:30.4032, lng:-97.7241, name:'Nerava Hub' };
  if (!deal) deal = {
    merchant_name: 'Coffee & Pastry',
    logo_url: 'https://dummyimage.com/112x112/f2f4f7/aaa.png&text=☕',
    copy: 'Free coffee w/ charging • 2–4pm',
    dist_miles: 0.3
  };

  // 2) Map inside rounded card
  const map = getMap([hub.lat, hub.lng], 15);
  // Optional: simple route dots to a mock merchant spot near hub
  const merchant = { lat: hub.lat - 0.005, lng: hub.lng + 0.002 };
  const route = L.polyline([[hub.lat,hub.lng],[merchant.lat,merchant.lng]], {
    color:'#3b82f6', weight:6, opacity:0.8, dashArray:'8 10'
  }).addTo(map);
  const bounds = L.latLngBounds([[hub.lat,hub.lng],[merchant.lat,merchant.lng]]);
  map.fitBounds(bounds, { padding:[24,24] });
  L.circleMarker([hub.lat,hub.lng],{radius:8,color:'#2563eb',fillColor:'#2563eb',fillOpacity:1}).addTo(map);
  L.circleMarker([merchant.lat,merchant.lng],{radius:8,color:'#2563eb',fillColor:'#2563eb',fillOpacity:1}).addTo(map);

  // 3) Perk card content
  const $ = s => document.querySelector(s);
  $('#perk-title').textContent = deal.merchant_name || 'Nearby perk';
  $('#perk-sub').textContent = deal.copy || 'Cheaper charging window';
  $('#perk-dist').textContent = (deal.dist_miles ? `${deal.dist_miles} mi from charger` : 'nearby');
  $('#perk-logo').src = deal.logo_url || 'https://dummyimage.com/112x112/f2f4f7/aaa.png&text=🏪';
  $('#perk-cta').onclick = () => window.setTab && window.setTab('charge');
  $('#btn-view-more').onclick = () => alert('Perk list coming soon');
}