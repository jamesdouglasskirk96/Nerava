// Core API utilities
window.Nerava = window.Nerava || {};
window.Nerava.core = window.Nerava.core || {};

const API_BASE = location.origin; // http://127.0.0.1:8001

// Check if API calls are safe (not file://)
function canCallApi() {
  return /^https?:/i.test(location.protocol);
}

// API helper function
async function apiJson(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'content-type': 'application/json' },
    ...opts,
  });
  if (!res.ok) throw new Error(`API ${path} ${res.status}`);
  return res.json();
}

// Optional: don't 404 when recommended hub API is absent
async function getRecommendedHubOrFallback() {
  try {
    const r = await fetch('/v1/hubs/recommended');
    if (r.ok) return await r.json();
  } catch (e) { /* ignore */ }
  // Fallback hub near Austin (example)
  return { id: 'demo_hub', name: 'Demo Hub', lat: 30.2672, lng: -97.7431 };
}

// Export to global namespace
window.Nerava.core.api = {
  API_BASE,
  canCallApi,
  apiJson,
  getRecommendedHubOrFallback
};
