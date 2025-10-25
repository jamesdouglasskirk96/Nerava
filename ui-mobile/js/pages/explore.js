import { apiGet } from '../core/api.js';
import { ensureMap } from '../app.js';
import { setTab } from '../app.js';

const $ = (s, r=document) => r.querySelector(s);

function fmtWalkMins(meters){
  const mins = Math.max(1, Math.round(meters / 80)); // ~80 m/min walking
  return `${mins} min walk`;
}
function haversine(a, b){
  if(!a || !b) return 0;
  const R=6371000, toRad=x=>x*Math.PI/180;
  const dLat = toRad((b.lat-a.lat)), dLng = toRad((b.lng-a.lng));
  const s1 = Math.sin(dLat/2)**2 + Math.cos(toRad(a.lat))*Math.cos(toRad(b.lat))*Math.sin(dLng/2)**2;
  return 2*R*Math.asin(Math.sqrt(s1));
}

function drawDashedRoute(map, charger, merchant) {
  if (!map || !charger || !merchant) return;
  
  // Clear existing route layers
  map.eachLayer(layer => {
    if (layer instanceof L.Polyline || layer instanceof L.CircleMarker) {
      map.removeLayer(layer);
    }
  });
  
  // Draw dashed route
  const route = L.polyline([[charger.lat, charger.lng], [merchant.lat, merchant.lng]], {
    color:'#3b82f6', weight:6, opacity:0.8, dashArray:'8 10'
  }).addTo(map);
  
  // Add markers
  L.circleMarker([charger.lat, charger.lng], {radius:8, color:'#2563eb', fillColor:'#2563eb', fillOpacity:1}).addTo(map);
  L.circleMarker([merchant.lat, merchant.lng], {radius:8, color:'#2563eb', fillColor:'#2563eb', fillOpacity:1}).addTo(map);
  
  // Fit bounds
  const bounds = L.latLngBounds([[charger.lat, charger.lng], [merchant.lat, merchant.lng]]);
  map.fitBounds(bounds, { padding:[24,24] });
}

function paintPerkUI(deal){
  $('#perk-ai-chip').textContent = '⚡ Recommended by Nerava AI';
  $('#perk-logo').src = deal.logo || 'https://dummyimage.com/112x112/f2f4f7/889/coffee.png&text=☕️';
  $('#perk-name').textContent = deal.name || 'Coffee & Pastry';
  $('#perk-address').textContent = deal.address || 'Domain Dr, Austin, TX';
  $('#perk-line').textContent = `${deal.offer || 'Free coffee 2–4pm'} • ${deal.walkText || '3 min walk from charger'}`;
  $('#perk-cta').onclick = () => setTab('charge');
}

export async function initExplore(){
  // Prevent duplicate initialization
  if (window.__exploreInitialized) return;
  window.__exploreInitialized = true;
  
  // 1) Data (soft-fail)
  let hub, deals;
  try { hub = await apiGet('/v1/hubs/recommend'); } catch(_) {}
  try { deals = await apiGet('/v1/deals/nearby'); } catch(_) {}

  const charger = hub?.lat && hub?.lng ? {lat:+hub.lat, lng:+hub.lng} : {lat:30.2682, lng:-97.7429};
  const merchant = deals?.[0]?.lat && deals?.[0]?.lng
    ? {lat:+deals[0].lat, lng:+deals[0].lng}
    : {lat:30.2658, lng:-97.7393};

  // 2) Map in rounded card
  const map = ensureMap(charger.lat, charger.lng, 15);
  if (!map) {
    console.warn('Map initialization failed');
    return;
  }
  drawDashedRoute(map, charger, merchant);

  // 3) Perk card paint
  const meters = haversine(charger, merchant);
  const deal = {
    name: deals?.[0]?.name || 'Coffee & Pastry',
    address: deals?.[0]?.address || '310 E 5th St, Austin, TX',
    logo: deals?.[0]?.logo,
    offer: deals?.[0]?.offer || 'Free coffee 2–4pm',
    walkText: `${fmtWalkMins(meters)} from charger`
  };
  paintPerkUI(deal);

  // 4) "View more" click
  $('#view-more')?.addEventListener('click', ()=> alert('Show all perks (list) — stub'));
}