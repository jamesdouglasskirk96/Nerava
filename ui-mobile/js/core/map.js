// Singleton Leaflet helpers for the mobile UI
/* globals L */
let _map = null;
let _routeLayer = null;

export function ensureMap(containerId = 'map', {lat=30.4025, lng=-97.7258, zoom=15} = {}) {
  const el = document.getElementById(containerId);
  if (!el) return null;

  if (_map) {
    // if container element was re-created, move the map into it
    if (_map._container !== el) {
      el.innerHTML = '';
      el.appendChild(_map._container);
      setTimeout(()=>_map.invalidateSize(), 0);
    } else {
      _map.invalidateSize();
    }
    return _map;
  }

  _map = L.map(el, { zoomControl: false, attributionControl: false })
          .setView([lat, lng], zoom);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
  }).addTo(_map);

  return _map;
}

export function clearRoute() {
  if (_routeLayer) {
    _routeLayer.remove();
    _routeLayer = null;
  }
}

export function drawRoute(points = [], {dashed=true} = {}) {
  if (!_map || points.length < 2) return;
  clearRoute();
  _routeLayer = L.polyline(points, {
    color: '#3B82F6',
    weight: 5,
    opacity: 0.9,
    dashArray: dashed ? '8,8' : null
  }).addTo(_map);
  fitBounds(points);
}

export function fitBounds(points, paddingPx = 48) {
  if (!_map || !points?.length) return;
  const b = L.latLngBounds(points);
  _map.fitBounds(b, { padding: [paddingPx, paddingPx], maxZoom: 17 });
}

export function addMerchantDot([lat, lng]) {
  if (!_map || !Number.isFinite(lat) || !Number.isFinite(lng)) return;
  L.circleMarker([lat, lng], {
    radius: 7, color:'#3B82F6', weight: 2, fillColor:'#3B82F6', fillOpacity:1
  }).addTo(_map);
}

export function addChargerDot([lat, lng]) {
  if (!_map || !Number.isFinite(lat) || !Number.isFinite(lng)) return;
  L.circleMarker([lat, lng], {
    radius: 7, color:'#0EA5E9', weight: 2, fillColor:'#0EA5E9', fillOpacity:1
  }).addTo(_map);
}