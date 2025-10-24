export function ensureMap(el = document.getElementById('map')) {
  if (!window.__leafletMap && el) {
    window.__leafletMap = L.map(el, { zoomControl: false }).setView([30.4021, -97.7265], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19, attribution: '&copy; OpenStreetMap'
    }).addTo(window.__leafletMap);
  }
  // Always invalidate & return the singleton
  setTimeout(() => window.__leafletMap.invalidateSize(), 0);
  return window.__leafletMap;
}

export function drawStraightRoute(a, b) {
  const m = ensureMap();
  if (window.__routeLayer) { m.removeLayer(window.__routeLayer); }
  window.__routeLayer = L.polyline([a, b], { color: '#3b82f6', weight: 5, dashArray: '8 8' }).addTo(m);
  m.fitBounds(L.latLngBounds([a, b]), { padding: [40, 40], maxZoom: 16 });
}