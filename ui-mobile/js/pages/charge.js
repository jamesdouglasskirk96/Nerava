// Charge page logic
window.Nerava = window.Nerava || {};
window.Nerava.pages = window.Nerava.pages || {};

// Load charge feed from API
async function loadChargeFeed() {
  const listEl = document.querySelector('#chargeFeedList');
  if (!listEl) return;
  listEl.innerHTML = `<div class="muted">Loading activity…</div>`;
  try {
    const items = await window.Nerava.core.api.apiJson('/v1/social/feed');
    if (!items.length) {
      listEl.innerHTML = `<div class="muted">No recent activity yet.</div>`;
      return;
    }
    listEl.innerHTML = items.map(renderFeedRow).join('');
    wireFollowChips(listEl, items);
  } catch (e) {
    console.error(e);
    listEl.innerHTML = `<div class="muted">Unable to load activity right now.</div>`;
  }
}

function renderFeedRow(it) {
  const amt = (it.gross_cents / 100).toFixed(2);
  const when = window.Nerava.core.utils.formatTime(it.timestamp);
  const sub = [it.meta?.hub_name, it.meta?.city].filter(Boolean).join(' · ');
  const initials = (it.user_id || '??').slice(0,2).toUpperCase();

  return `
  <div class="feed-row" data-user="${it.user_id}">
    <div class="avatar">${initials}</div>
    <div class="feed-main">
      <div class="title"><b>${it.user_id}</b> earned $${amt}${it.meta?.kwh ? ` for ${it.meta.kwh} kWh` : ''}</div>
      <div class="sub">${sub || 'Nerava'}</div>
      <div class="meta muted">${when}</div>
    </div>
    <button class="chip follow-chip" data-user="${it.user_id}" aria-label="Follow ${it.user_id}">
      Follow
    </button>
  </div>`;
}

async function isFollowing(me, other) {
  if (!window.Nerava.core.api.canCallApi()) return false;
  const following = await window.Nerava.core.api.apiJson(`/v1/social/following?user_id=${encodeURIComponent(me)}`);
  return following.some(f => f.followee_id === other);
}

function wireFollowChips(scopeEl, items) {
  const me = window.NERAVA_USER_ID || 'you';
  scopeEl.querySelectorAll('.follow-chip').forEach(async btn => {
    const other = btn.dataset.user;
    if (other === me) { btn.remove(); return; }
    try {
      if (await isFollowing(me, other)) btn.classList.add('following'), btn.textContent = 'Following';
    } catch {}
    btn.addEventListener('click', async () => {
      const following = btn.classList.toggle('following');
      btn.textContent = following ? 'Following' : 'Follow';
      try {
        await window.Nerava.core.api.apiJson('/v1/social/follow', {
          method: 'POST',
          body: JSON.stringify({
            follower_id: me,
            followee_id: other,
            follow: following
          })
        });
      } catch (e) {
        btn.classList.toggle('following');
        btn.textContent = btn.classList.contains('following') ? 'Following' : 'Follow';
      }
    });
  });
}

async function initCharge() {
  // Initialize map for route to charger
  await initChargeMap();
  
  // Load social feed
  loadChargeFeed();
}

async function initChargeMap() {
  // Wait for Leaflet to be available
  if (!window.L) {
    setTimeout(initChargeMap, 100);
    return;
  }
  
  const mapEl = document.getElementById('chargeMap');
  if (!mapEl) return;
  
  // Initialize map
  const map = L.map('chargeMap').setView([37.7749, -122.4194], 13);
  
  // Add tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);
  
  // Get user location and show route to nearest charger
  try {
    const userPos = await getUserLocation();
    const chargerPos = await getNearestCharger();
    
    // Add markers
    L.marker([userPos.lat, userPos.lng]).addTo(map)
      .bindPopup('Your location');
    
    L.marker([chargerPos.lat, chargerPos.lng]).addTo(map)
      .bindPopup('Charging station');
    
    // Draw route if routing is available
    if (L.Routing && L.Routing.control) {
      const routeControl = L.Routing.control({
        waypoints: [
          L.latLng(userPos.lat, userPos.lng),
          L.latLng(chargerPos.lat, chargerPos.lng)
        ],
        addWaypoints: false,
        draggableWaypoints: false,
        routeWhileDragging: false,
        show: false,
        fitSelectedRoutes: true,
        lineOptions: {
          styles: [{ color: '#2a6bf2', weight: 6, opacity: 0.95 }]
        }
      });
      
      routeControl.addTo(map);
      
      routeControl.on('routesfound', (e) => {
        const route = e.routes[0];
        const summary = route.summary;
        const distance = (summary.totalDistance / 1609.34).toFixed(1);
        const time = Math.round(summary.totalTime / 60);
        
        // Update the perk stats with real route data
        const statsEl = document.querySelector('.perk-stats');
        if (statsEl) {
          statsEl.innerHTML = `<span>~${time} min</span><span>•</span><span>${distance} mi</span>`;
        }
      });
    } else {
      // Fallback: draw straight line
      L.polyline([
        [userPos.lat, userPos.lng],
        [chargerPos.lat, chargerPos.lng]
      ], { color: '#2a6bf2', weight: 5, opacity: 0.9 }).addTo(map);
      
      // Fit bounds to show both points
      map.fitBounds([
        [userPos.lat, userPos.lng],
        [chargerPos.lat, chargerPos.lng]
      ], { padding: [20, 20] });
    }
    
  } catch (error) {
    console.error('Error initializing charge map:', error);
    // Show default map centered on SF
    map.setView([37.7749, -122.4194], 13);
  }
}

async function getUserLocation() {
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

async function getNearestCharger() {
  // Try to get from API, fallback to static location
  try {
    const hub = await window.Nerava.core.api.apiJson('/v1/hubs/recommended');
    if (hub && hub.lat && hub.lng) {
      return { lat: hub.lat, lng: hub.lng };
    }
  } catch (error) {
    console.log('Using fallback charger location');
  }
  
  // Fallback charger location
  return { lat: 37.7849, lng: -122.4094 };
}

// Export init function
window.Nerava.pages.charge = {
  init: initCharge
};

// Also make it globally available for app.js
window.initCharge = initCharge;
