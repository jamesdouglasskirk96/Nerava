// Map utilities and routing helpers
window.Nerava = window.Nerava || {};
window.Nerava.core = window.Nerava.core || {};

let exploreMap = null;
let exploreRouteCtl = null;

// Initialize map
function ensureMap() {
  if (!exploreMap && window.L) {
    exploreMap = L.map('mapContainer').setView([37.7749, -122.4194], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(exploreMap);
  }
  return exploreMap;
}

// Check if Leaflet Routing Machine is available
function hasLRM() {
  return !!(window.L && L.Routing && L.Routing.control);
}

// Draw route with fallback
async function drawMinimalRouteTo(hub) {
  if (!L || !exploreMap) return;

  // fallback start ~near hub
  const startFallback = [hub.lat + 0.01, hub.lng + 0.01];
  const getStart = () => new Promise(resolve => {
    if (!navigator.geolocation) return resolve(startFallback);
    navigator.geolocation.getCurrentPosition(
      p => resolve([p.coords.latitude, p.coords.longitude]),
      () => resolve(startFallback),
      { enableHighAccuracy: true, maximumAge: 60000, timeout: 4000 }
    );
  });

  const start = await getStart();

  // Clear previous graphics
  if (exploreRouteCtl?.getPlan) { try { exploreMap.removeControl(exploreRouteCtl); } catch {} }
  if (window.__exploreFallbackLayer) { try { exploreMap.removeLayer(window.__exploreFallbackLayer); } catch {} }
  if (window.__exploreMarkers) { window.__exploreMarkers.forEach(m => exploreMap.removeLayer(m)); }
  window.__exploreMarkers = [];

  // Prefer routing plugin if available
  if (hasLRM()) {
    exploreRouteCtl = L.Routing.control({
      waypoints: [ L.latLng(start[0], start[1]), L.latLng(hub.lat, hub.lng) ],
      addWaypoints: false, draggableWaypoints: false, fitSelectedRoutes: true, show: false
    }).addTo(exploreMap);

    exploreRouteCtl.on('routesfound', e => {
      const r = e.routes?.[0];
      const etaMin = Math.round((r?.summary?.totalTime || 0) / 60);
      const miles = ( (r?.summary?.totalDistance || 0) / 1609.34 );
      document.getElementById('routeEta').textContent = etaMin ? `~${etaMin} min` : '—';
      document.getElementById('routeMiles').textContent = isFinite(miles) ? `${miles.toFixed(1)} mi` : '—';
    });

    return; // we're done
  }

  // --- Fallback (no routing plugin) ---
  const line = L.polyline([ start, [hub.lat, hub.lng] ], { color: '#2a6bf2', weight: 4, opacity: 0.8 });
  window.__exploreFallbackLayer = line.addTo(exploreMap);
  const startMarker = L.marker(start).addTo(exploreMap);
  const hubMarker = L.marker([hub.lat, hub.lng]).addTo(exploreMap);
  window.__exploreMarkers.push(startMarker, hubMarker);
  exploreMap.fitBounds(line.getBounds(), { padding: [40, 40] });

  // Compute simple crow-flies stats
  const miles = haversineMiles(start, [hub.lat, hub.lng]);
  document.getElementById('routeMiles').textContent = `${miles.toFixed(1)} mi`;
  document.getElementById('routeEta').textContent = '—';
}

// Haversine distance calculation
function haversineMiles(coord1, coord2) {
  const R = 3959; // Earth's radius in miles
  const dLat = (coord2[0] - coord1[0]) * Math.PI / 180;
  const dLon = (coord2[1] - coord1[1]) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(coord1[0] * Math.PI / 180) * Math.cos(coord2[0] * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

// Export to global namespace
window.Nerava.core.map = {
  ensureMap,
  hasLRM,
  drawMinimalRouteTo,
  haversineMiles
};
