// Explore page logic
window.Nerava = window.Nerava || {};
window.Nerava.pages = window.Nerava.pages || {};

// Guard: wait for Leaflet presence + DOM ready
(function ensureLeafletReady(){
  if (document.readyState !== 'complete' && document.readyState !== 'interactive') {
    document.addEventListener('DOMContentLoaded', ensureLeafletReady, { once: true });
    return;
  }
  if (!window.L) {
    // Try again shortly; don't crash
    setTimeout(ensureLeafletReady, 50);
    return;
  }
  // Proceed to init (wrap existing init Explore here)
  window.initExplore && window.initExplore();
})();

const FALLBACK_HUB = { id: 'demo-hub', lat: 37.7749, lng: -122.4194, name: 'Demo Hub' };
const FALLBACK_PERK = { id: 'demo-perk', title: 'Free Coffee', description: 'Get a free coffee with any charge', value: '$3.50' };

// Guard routing usage in Explore (no plugin, no crash)
async function drawRoute(fromLatLng, toLatLng) {
  if (!window.L) return; // Leaflet missing, bail gracefully

  // Clear any prior layer
  if (window._neravaRoute) {
    window._neravaRoute.remove();
    window._neravaRoute = null;
  }

  // Prefer routing plugin when present
  if (L.Routing && L.Routing.control) {
    try {
      window._neravaRoute = L.Routing.control({
        waypoints: [ L.latLng(fromLatLng[0], fromLatLng[1]), L.latLng(toLatLng[0], toLatLng[1]) ],
        addWaypoints: false, draggableWaypoints: false, fitSelectedRoutes: true, routeWhileDragging: false
      }).addTo(map);
      return;
    } catch (e) {
      console.warn('Routing plugin failed; using polyline fallback.', e);
    }
  }

  // Fallback: straight polyline + fit bounds
  const line = L.polyline([fromLatLng, toLatLng], { weight: 4, opacity: 0.9 });
  line.addTo(map);
  map.fitBounds(line.getBounds(), { padding: [24, 24] });
  window._neravaRoute = line;
}

async function loadRecommendedHub(){
  const live = await window.Nerava.core.api.apiJson('/v1/hubs/recommended');
  if (live && live.lat && live.lng) return live;

  // fallback data near Austin (adjust as needed)
  return { id: 'fallback_hub', name: 'Nerava Hub', lat: 30.2672, lng: -97.7431 };
}

async function getRecommendedHub() {
  if (!window.Nerava.core.api.canCallApi()) return FALLBACK_HUB;
  try {
    const r = await window.Nerava.core.api.apiJson('/v1/hubs/recommended');
    if (!r.ok) throw 0;
    const [first] = await r.json();
    return first || FALLBACK_HUB;
  } catch { return FALLBACK_HUB; }
}

async function getPreferredPerk(hubId) {
  if (!window.Nerava.core.api.canCallApi()) return FALLBACK_PERK;
  try {
    // Try ML recommendations first
    const mlRecs = await window.Nerava.core.api.apiJson(`/v1/ml/recommend/perks?hub_id=${encodeURIComponent(hubId)}&user_id=current_user`);
    if (mlRecs.recommendations && mlRecs.recommendations.length > 0) {
      const topPerk = mlRecs.recommendations[0].perk;
      return {
        id: topPerk.id,
        title: topPerk.name,
        description: topPerk.description,
        value: `$${(topPerk.value_cents / 100).toFixed(2)}`
      };
    }
    
    // Fallback to regular perks
    const r = await window.Nerava.core.api.apiJson(`/v1/places/perks?hub_id=${encodeURIComponent(hubId)}`);
    if (!r.ok) throw 0;
    const list = await r.json();
    return list?.[0] || FALLBACK_PERK;
  } catch { return FALLBACK_PERK; }
}

async function drawRouteOrFallback(map, from, to) {
  // Ensure Leaflet loaded
  if (!window.L || !map) return;

  // If routing plugin missing, draw fallback polyline
  const drawFallback = () => {
    const line = L.polyline([from, to], { color: '#2a6bf2', weight: 5, opacity: 0.9 }).addTo(map);
    map.fitBounds(line.getBounds(), { padding: [50, 50] });
    return { fallback: true };
  };

  try {
    if (!L.Routing || !L.Routing.control) {
      console.warn('Routing plugin missing, using fallback line.');
      return drawFallback();
    }

    // Clean up old control if we re-initialize
    if (window.__routeCtl) {
      map.removeControl(window.__routeCtl);
      window.__routeCtl = null;
    }

    const ctl = L.Routing.control({
      waypoints: [ L.latLng(from.lat, from.lng), L.latLng(to.lat, to.lng) ],
      addWaypoints: false,
      draggableWaypoints: false,
      routeWhileDragging: false,
      show: false,
      fitSelectedRoutes: true,
      lineOptions: { styles: [{ color: '#2a6bf2', weight: 6, opacity: 0.95 }] }
    });

    ctl.addTo(map);
    window.__routeCtl = ctl;

    ctl.on('routesfound', (e) => {
      const sum = e.routes?.[0]?.summary;
      if (sum) {
        const mins = Math.round(sum.totalTime / 60);
        const miles = (sum.totalDistance / 1609.34).toFixed(1);
        const etaEl = document.querySelector('#perkEta');
        const milesEl = document.querySelector('#perkMiles');
        if (etaEl) etaEl.textContent = `~${mins} min`;
        if (milesEl) milesEl.textContent = `${miles} mi`;
      }
    });

    return { fallback: false };
  } catch (err) {
    console.error('Routing failed, using fallback', err);
    return drawFallback();
  }
}

// when routing plugin is missing, show a small inline note once
function noteRoutingFallback(){
  const el = document.getElementById('perkMiles');
  if (!el) return;
  if (window._notedRouting) return; window._notedRouting = true;
  el.textContent = '— mi (routing add-on not loaded)';
}

async function initExploreMinimal() {
  const map = window.Nerava.core.map.ensureMap();
  if (!map) return;

  const hub = await loadRecommendedHub();
  const perk = await getPreferredPerk(hub.id);

  // Update UI
  document.getElementById('perkTitle').textContent = perk.title || 'Special Offer';
  document.getElementById('perkSub').textContent = perk.description || 'Free coffee with any charge';

  // Get user location and draw route
  const user = await getUserLocationFallback();
  const result = await drawRouteOrFallback(map, user, hub);
  
  // Show fallback note if routing failed
  if (result && result.fallback) {
    noteRoutingFallback();
  }
  
  // Wire up "View more" button
  document.getElementById('perkMoreBtn')?.addEventListener('click', () => {
    // Switch to Claim tab
    const claimTab = document.getElementById('tabScan');
    if (claimTab) claimTab.click();
  });
}

async function getUserLocationFallback() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve({ lat: 37.7849, lng: -122.4094 }); // Default SF location
      return;
    }
    
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve({ lat: 37.7849, lng: -122.4094 }), // Fallback
      { enableHighAccuracy: true, maximumAge: 60000, timeout: 4000 }
    );
  });
}

// Export init function
window.Nerava.pages.explore = {
  init: initExploreMinimal
};

// Attach to window for the guard
window.initExplore = initExploreMinimal;
