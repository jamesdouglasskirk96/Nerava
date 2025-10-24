// Claim page logic
window.Nerava = window.Nerava || {};
window.Nerava.pages = window.Nerava.pages || {};

let claimWatchId = null;

function startClaimGeolocation() {
  if (claimWatchId) {
    navigator.geolocation.clearWatch(claimWatchId);
  }
  
  if (!navigator.geolocation) {
    console.warn('Geolocation not supported');
    return;
  }

  claimWatchId = navigator.geolocation.watchPosition(
    (position) => {
      updateClaimUI(position.coords);
    },
    (error) => {
      console.warn('Geolocation error:', error);
    },
    {
      enableHighAccuracy: true,
      maximumAge: 30000,
      timeout: 10000
    }
  );
}

function updateClaimUI(coords) {
  const lat = coords.latitude.toFixed(6);
  const lng = coords.longitude.toFixed(6);
  
  const locationEl = document.getElementById('claimLocation');
  if (locationEl) {
    locationEl.textContent = `${lat}, ${lng}`;
  }
}

function initClaim() {
  startClaimGeolocation();
}

// Export init function
window.Nerava.pages.claim = {
  init: initClaim
};
