import { ensureMap, drawStraightRoute } from '../core/map.js';
import { apiGet } from '../core/api.js';

export async function initExplore() {
  // Always ensure map is initialized
  ensureMap();

  // Try API, but fall back to demo coordinates on 404/Network
  let hub, deal;
  try {
    hub = await apiGet('/v1/hubs/recommend');
  } catch (_) {}
  try {
    const deals = await apiGet('/v1/deals/nearby');
    deal = deals?.[0];
  } catch (_) {}

  // Use API data if available, otherwise fallback coordinates
  const charger = [
    (hub?.lat && Number.isFinite(hub.lat)) ? hub.lat : 30.4062,
    (hub?.lng && Number.isFinite(hub.lng)) ? hub.lng : -97.7260,
  ];
  const merchant = [
    (deal?.lat && Number.isFinite(deal.lat)) ? deal.lat : 30.3990,
    (deal?.lng && Number.isFinite(deal.lng)) ? deal.lng : -97.7230,
  ];

  // Draw straight route
  drawStraightRoute(charger, merchant);

  // Simple perk card with fallback data
  const card = document.getElementById('perk-card');
  if (card) {
    const merchantName = deal?.name || 'Nearby perk';
    const merchantReward = deal?.reward_text || 'Cheaper during Green Hour';
    const merchantWindow = deal?.window || '2–4pm';
    const merchantDistance = deal?.distance_text || '0.3 mi from charger';

    card.innerHTML = `
      <div class="perk-card">
        <div class="ai-chip">⚡ Recommended by Nerava AI</div>
        <div class="perk-body">
          <div class="logo">☕</div>
          <div class="info">
            <h3>${merchantName}</h3>
            <p>${merchantReward} • ${merchantWindow}<br/>
            ${merchantDistance}</p>
          </div>
          <button id="btn-charge-here" class="btn btn-primary">Charge here</button>
        </div>
      </div>
    `;
    document.getElementById('btn-charge-here')?.addEventListener('click', () => {
      // Switch to charge tab
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelector('[data-tab="charge"]')?.classList.add('active');
      document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
      document.getElementById('page-charge')?.classList.remove('hidden');
    });
  }

  document.getElementById('btn-view-more')?.addEventListener('click', () => alert('List of perks based on your preferences (coming soon)'));
}

// boot when page shown
document.addEventListener('DOMContentLoaded', ()=> initExplore());