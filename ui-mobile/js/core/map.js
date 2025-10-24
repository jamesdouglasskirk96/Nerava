/* globals L */
// Singleton Leaflet map + helpers. Safe to import from any page script.
let _map = null;
let _routeLayer = null;

export function ensureMap(containerId = 'map', opts = {}) {
  const el = document.getElementById(containerId);
  if (!el) return null;
  if (_map) {
    // If a previous map is mounted on a different element, detach and reattach
    if (_map._container !== el) {
      el.innerHTML = '';
      _map = null;
    } else {
      setTimeout(() => _map.invalidateSize(), 0);
      return _map;
    }
  }
  _map = L.map(el, { zoomControl: false, attributionControl: false }).setView(
    [30.4021, -97.7265],
    15
  );
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
  }).addTo(_map);
  setTimeout(() => _map.invalidateSize(), 0);
  return _map;
}

export function clearRoute() {
  if (_routeLayer) {
    _routeLayer.remove();
    _routeLayer = null;
  }
}

export function drawStraightRoute(a, b) {
  if (!_map || !a || !b) return;
  clearRoute();
  _routeLayer = L.layerGroup().addTo(_map);
  const line = L.polyline([a, b], {
    color: '#3b82f6',
    weight: 5,
    opacity: 0.7,
    dashArray: '8 8'
  }).addTo(_routeLayer);
  L.circleMarker(a, { radius: 7, color: '#2563eb', fillColor: '#2563eb', fillOpacity: 1 }).addTo(_routeLayer);
  L.circleMarker(b, { radius: 7, color: '#2563eb', fillColor: '#2563eb', fillOpacity: 1 }).addTo(_routeLayer);
  _map.fitBounds(line.getBounds(), { padding: [28, 28], maxZoom: 17 });
}

export function fitBounds(bounds) {
  if (_map && bounds) _map.fitBounds(bounds, { padding: [28, 28], maxZoom: 17 });
}