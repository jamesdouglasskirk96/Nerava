// ui-mobile/js/core/map.js
/* globals L */

let _map = null, _route = null, _markers = [];

export function ensureMap(elId = 'map', center = [30.4025, -97.7258], zoom = 15) {
  const el = document.getElementById(elId);
  if (!el) return null;
  if (_map) { 
    setTimeout(() => _map.invalidateSize(), 0); 
    return _map; 
  }
  _map = L.map(elId, { zoomControl: false }).setView(center, zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(_map);
  return _map;
}

export function clearRoute() {
  if (_route) { 
    _map.removeLayer(_route); 
    _route = null; 
  }
  _markers.forEach(m => _map.removeLayer(m)); 
  _markers.length = 0;
}

export function drawWalkingRoute(a, b) {
  if (!_map || !a || !b) return;
  clearRoute();
  const latlngs = [a, b];
  _route = L.polyline(latlngs, { dashArray: '6,6', weight: 4, color: '#2563eb', opacity: .9 }).addTo(_map);
  _markers.push(L.circleMarker(a, { radius: 6, color: '#2563eb', fillOpacity: 1 }).addTo(_map));
  _markers.push(L.circleMarker(b, { radius: 6, color: '#2563eb', fillOpacity: 1 }).addTo(_map));
  const pad = { paddingTopLeft: [16, 16], paddingBottomRight: [16, 96], maxZoom: 17 };
  _map.fitBounds(_route.getBounds(), pad);
}
