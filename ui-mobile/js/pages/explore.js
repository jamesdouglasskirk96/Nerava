import { apiGet } from '../core/api.js';
import { ensureMap } from '../app.js';

// Safe map initialization that prevents duplicate initialization
const getMap = (center=[30.4025,-97.7258], zoom=14) => {
  // Use the existing ensureMap from app.js which has proper duplicate prevention
  if (window.ensureMap) {
    return window.ensureMap(center[0], center[1], zoom);
  }
  
  // Fallback: check if map already exists and return it
  const mapElement = document.getElementById('map');
  if (!mapElement) return null;
  
  // Check if Leaflet map already exists on this element
  if (mapElement._leaflet_id) {
    // Try to get existing map instance, fallback to creating new one if fails
    try {
      return L.Map.get(mapElement._leaflet_id);
    } catch (e) {
      // If getting existing map fails, clear the element and create new one
      mapElement.innerHTML = '';
      delete mapElement._leaflet_id;
    }
  }
  
  // Only create new map if none exists
  const map = L.map('map', { zoomControl:false }).setView(center, zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{ maxZoom:19 }).addTo(map);
  return map;
};

export async function initExplore(){
  // Prevent duplicate initialization
  if (window.__exploreInitialized) return;
  window.__exploreInitialized = true;
  
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
  if (!map) {
    console.warn('Map initialization failed');
    return;
  }
  
  // Clear any existing layers before adding new ones
  map.eachLayer(layer => {
    if (layer instanceof L.Polyline || layer instanceof L.CircleMarker) {
      map.removeLayer(layer);
    }
  });
  
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