// Explore page logic
window.Nerava = window.Nerava || {};
window.Nerava.pages = window.Nerava.pages || {};

const FALLBACK_HUB = { id: 'demo-hub', lat: 37.7749, lng: -122.4194, name: 'Demo Hub' };
const FALLBACK_PERK = { id: 'demo-perk', title: 'Free Coffee', description: 'Get a free coffee with any charge', value: '$3.50' };

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
    const r = await window.Nerava.core.api.apiJson(`/v1/places/perks?hub_id=${encodeURIComponent(hubId)}`);
    if (!r.ok) throw 0;
    const list = await r.json();
    return list?.[0] || FALLBACK_PERK;
  } catch { return FALLBACK_PERK; }
}

async function initExploreMinimal() {
  const map = window.Nerava.core.map.ensureMap();
  if (!map) return;

  const hub = await getRecommendedHub();
  const perk = await getPreferredPerk(hub.id);

  // Update UI
  document.getElementById('hubName').textContent = hub.name || 'Charging Hub';
  document.getElementById('perkTitle').textContent = perk.title || 'Special Offer';
  document.getElementById('perkValue').textContent = perk.value || '$3.50';

  // Draw route
  await window.Nerava.core.map.drawMinimalRouteTo(hub);
}

// Export init function
window.Nerava.pages.explore = {
  init: initExploreMinimal
};
