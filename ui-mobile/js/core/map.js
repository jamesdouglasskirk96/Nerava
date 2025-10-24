// ui-mobile/js/core/map.js
/* globals L */

let map; // shared singleton for the whole app
let mapContainerId = 'map'; // default id; can be overridden by caller

export function ensureMap(lat = 30.4021, lng = -97.7258, options = {}) {
  const el = document.getElementById(mapContainerId) || document.getElementById('map');
  if (!el) return null;
  // If a Leaflet instance already attached to this element, reuse it.
  if (map && map._leaflet_id) {
    map.invalidateSize();
    return map;
  }
  // Defensive: if element got a map previously, clear it.
  if (el._leaflet_id) {
    try { el._leaflet_id = undefined; el.innerHTML = ''; } catch {}
  }
  map = L.map(el, { zoomControl: false, ...options }).setView([lat, lng], 16);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(map);
  return map;
}

export function setMapContainerId(id) { mapContainerId = id; }

let _route = null, _markers = [];

export function clearRoute() {
  if (_route) { 
    map.removeLayer(_route); 
    _route = null; 
  }
  _markers.forEach(m => map.removeLayer(m)); 
  _markers.length = 0;
}

export function drawWalkingRoute(a, b) {
  if (!map || !a || !b) return;
  clearRoute();
  const latlngs = [a, b];
  _route = L.polyline(latlngs, { dashArray: '6,6', weight: 4, color: '#2563eb', opacity: .9 }).addTo(map);
  _markers.push(L.circleMarker(a, { radius: 6, color: '#2563eb', fillOpacity: 1 }).addTo(map));
  _markers.push(L.circleMarker(b, { radius: 6, color: '#2563eb', fillOpacity: 1 }).addTo(map));
  const pad = { paddingTopLeft: [16, 16], paddingBottomRight: [16, 96], maxZoom: 17 };
  map.fitBounds(_route.getBounds(), pad);
}
