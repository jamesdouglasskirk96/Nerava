// ui-mobile/js/core/map.js
/* globals L */

// singletons so we reuse the same map/layers
let _map = null;

function hideAttribution() {
  const ctrl = document.querySelector('.leaflet-control-attribution');
  const wrap = document.querySelector('.leaflet-bottom.leaflet-right');
  if (ctrl) ctrl.style.display = 'none';
  if (wrap) wrap.style.display = 'none';
}

/**
 * Ensure a Leaflet map exists in the given container.
 * Returns the map instance.
 */
export function ensureMap({ containerId = 'map', lat = 30.4021, lng = -97.7265, zoom = 15 } = {}) {
  const el = document.getElementById(containerId);
  if (!el) return null;

  if (_map) {
    try { _map.invalidateSize(); } catch {}
    return _map;
  }

  _map = L.map(el, { zoomControl: false }).setView([lat, lng], zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(_map);

  // hide attribution now and on subsequent loads/resizes
  setTimeout(hideAttribution, 150);
  _map.on('load', hideAttribution);
  _map.whenReady(hideAttribution);

  return _map;
}

/**
 * Fit the map to two points and optionally draw a straight line route.
 */
export function fitAndDrawStraight({ from, to, options = {} } = {}) {
  const m = _map;
  if (!m || !from || !to) return;

  const { padding = [40, 80], maxZoom = 16, color = '#3b82f6' } = options;

  // remove any previous temp route layer
  if (m._neravaStraightRoute) {
    try { m.removeLayer(m._neravaStraightRoute); } catch {}
  }

  const latlngs = [from, to];
  const poly = L.polyline(latlngs, { color, weight: 4, opacity: 0.9, dashArray: '6,6' }).addTo(m);
  m._neravaStraightRoute = poly;

  try { m.fitBounds(L.latLngBounds(latlngs), { padding, maxZoom }); } catch {}
}

export function getMap() { return _map; }