// ui-mobile/js/core/map.js
/* globals L */

// Singleton map instance and container tracking
let MAP = null;
let MAP_CONTAINER_ID = null;

function hideAttribution() {
  const ctrl = document.querySelector('.leaflet-control-attribution');
  const wrap = document.querySelector('.leaflet-bottom.leaflet-right');
  if (ctrl) ctrl.style.display = 'none';
  if (wrap) wrap.style.display = 'none';
}

/**
 * Ensure a Leaflet map exists in the given container.
 * Returns the map instance. Idempotent - safe to call multiple times.
 */
export function ensureMap(containerId = 'map', lat = 30.4021, lng = -97.7265, zoom = 15) {
  const el = document.getElementById(containerId);
  if (!el) return null;

  // If called again with same container, return existing map and invalidate size
  if (MAP && MAP_CONTAINER_ID === containerId) {
    queueMicrotask(() => {
      try { MAP.invalidateSize(); } catch {}
    });
    return MAP;
  }

  // If DOM element already has a Leaflet instance, clone to fresh element
  if (el._leaflet_id) {
    const old = el;
    const fresh = el.cloneNode(false);
    old.parentNode.replaceChild(fresh, old);
    el = fresh;
  }

  // If MAP exists but container differs, remove old map
  if (MAP && MAP_CONTAINER_ID !== containerId) {
    try { MAP.remove(); } catch {}
    MAP = null;
    MAP_CONTAINER_ID = null;
  }

  // Create new map instance
  MAP = L.map(el, { zoomControl: false }).setView([lat, lng], zoom);
  MAP_CONTAINER_ID = containerId;
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(MAP);

  // hide attribution now and on subsequent loads/resizes
  setTimeout(hideAttribution, 150);
  MAP.on('load', hideAttribution);
  MAP.whenReady(hideAttribution);

  return MAP;
}

/**
 * Get the current map instance
 */
export function getMap() { return MAP; }

/**
 * Invalidate map size (safe to call multiple times)
 */
export function invalidateMap() {
  if (MAP) {
    try { MAP.invalidateSize(); } catch {}
  }
}

/**
 * Safely fit bounds with error handling
 */
export function fitBoundsSafe(bounds, options = {}) {
  if (!MAP || !bounds) return;
  try { 
    MAP.fitBounds(bounds, { padding: [24, 24], maxZoom: 16, ...options }); 
  } catch {}
}

/**
 * Fit the map to two points and optionally draw a straight line route.
 */
export function fitAndDrawStraight({ from, to, options = {} } = {}) {
  if (!MAP || !from || !to) return;

  const { padding = [40, 80], maxZoom = 16, color = '#3b82f6' } = options;

  // remove any previous temp route layer
  if (MAP._neravaStraightRoute) {
    try { MAP.removeLayer(MAP._neravaStraightRoute); } catch {}
  }

  const latlngs = [from, to];
  const poly = L.polyline(latlngs, { color, weight: 4, opacity: 0.9, dashArray: '6,6' }).addTo(MAP);
  MAP._neravaStraightRoute = poly;

  fitBoundsSafe(L.latLngBounds(latlngs), { padding, maxZoom });
}