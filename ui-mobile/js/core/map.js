/* globals L */
let _map = null;
let _overlays = [];

export function ensureMap(containerId = 'map', { lat = 30.4025, lng = -97.7258, zoom = 15 } = {}) {
  const el = document.getElementById(containerId);
  if (!el) return null;

  // Reuse existing map if already bound to same container
  if (_map && _map._container === el) {
    _map.invalidateSize();
    return _map;
  }

  // If a map exists on a different container, remove it first
  if (_map) {
    try { _map.remove(); } catch {}
    _map = null;
    _overlays = [];
  }

  _map = L.map(el, { zoomControl: false }).setView([lat, lng], zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '' // we'll hide attribution via CSS
  }).addTo(_map);
  return _map;
}

export function addOverlay(layer) {
  if (_map && layer) { layer.addTo(_map); _overlays.push(layer); }
}

export function clearOverlays() {
  if (!_map) return;
  _overlays.forEach(l => { try { _map.removeLayer(l); } catch {} });
  _overlays = [];
}

export function fitBounds(bounds, padding = [60, 60], maxZoom = 17) {
  if (_map && bounds) _map.fitBounds(bounds, { padding, maxZoom });
}

export function getMap() { return _map; }