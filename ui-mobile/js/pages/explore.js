import { ensureMap, fitMapToRoute, drawDashedRoute, placeCircle, mapRef } from '../js/core/map.js';
import { apiGet } from '../core/api.js';

export async function initExplore(){
  // Safe fallbacks if backend 404s
  let hub = null, deal = null;
  try { hub = await apiGet('/v1/hubs/recommend'); } catch(_) {}
  try { deal = await apiGet('/v1/deals/nearby'); } catch(_) {}

  // Fallback coordinates (Domain, Austin) if APIs unavailable
  const charger = {
    lat: Number(hub?.lat ?? 30.4025),
    lng: Number(hub?.lng ?? -97.7258)
  };
  const merchant = {
    lat: Number(deal?.items?.[0]?.lat ?? 30.2729),
    lng: Number(deal?.items?.[0]?.lng ?? -97.7413)
  };

  ensureMap('map', [charger.lat, charger.lng], 15);

  // Clear & draw simple route/markers
  placeCircle(charger.lat, charger.lng, { radius:9 });
  placeCircle(merchant.lat, merchant.lng, { radius:9 });
  drawDashedRoute(charger, merchant);
  fitMapToRoute(charger, merchant, 60);

  // Simple perk card with fallback data
  const card = document.getElementById('perk-card');
  if (card) {
    const merchantName = deal?.items?.[0]?.name || 'Nearby perk';
    const merchantReward = deal?.items?.[0]?.reward_text || 'Cheaper during Green Hour';
    const merchantWindow = deal?.items?.[0]?.window || '2–4pm';
    const merchantDistance = deal?.items?.[0]?.distance_text || '0.3 mi from charger';

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