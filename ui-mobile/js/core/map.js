export let mapRef = null;
let tileLayerRef = null;

export function ensureMap(elId = 'map', center = [30.4025, -97.7258], zoom = 15) {
  // Idempotent map boot
  const el = document.getElementById(elId);
  if (!el) return null;

  // Leaflet throws if reusing the same element; clear previous instance safely
  if (mapRef && mapRef._container === el) {
    mapRef.invalidateSize();
    return mapRef;
  }
  if (mapRef) {
    try { mapRef.remove(); } catch (_) {}
    mapRef = null;
    tileLayerRef = null;
  }

  mapRef = L.map(el, { zoomControl: false }).setView(center, clampZoom(zoom));
  tileLayerRef = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '&copy; OpenStreetMap'
  }).addTo(mapRef);
  return mapRef;
}

export function clampZoom(z) { return Math.max(13, Math.min(17, Number(z)||15)); }

export function fitMapToRoute(a, b, padPx = 60) {
  if (!mapRef) return;
  if (!isFinite(a?.lat) || !isFinite(a?.lng) || !isFinite(b?.lat) || !isFinite(b?.lng)) return;
  const bounds = L.latLngBounds([ [a.lat, a.lng], [b.lat, b.lng] ]);
  mapRef.fitBounds(bounds, { padding: [padPx, padPx], maxZoom: 16 });
}

export function drawDashedRoute(a, b) {
  if (!mapRef) return null;
  const latlngs = [[a.lat, a.lng], [b.lat, b.lng]];
  return L.polyline(latlngs, { color:'#4178f7', weight:6, opacity:0.8, dashArray:'8,10' }).addTo(mapRef);
}

export function placeCircle(lat, lng, opts={}) {
  if (!mapRef || !isFinite(lat) || !isFinite(lng)) return null;
  return L.circleMarker([lat, lng], {
    radius: 8, color:'#4178f7', fillColor:'#4178f7', fillOpacity:1, ...opts
  }).addTo(mapRef);
}