import { ensureMap, drawRoute, fitBounds, addMerchantDot, addChargerDot, clearRoute } from '../core/map.js';
import { apiGet } from '../core/api.js';

export async function initExplore() {
  const m = ensureMap('map');
  if (m) {
    const charger = [30.4025, -97.7258]; // fallback
    const merch = [30.4033, -97.7240]; // fallback

    try {
      const rec = await apiGet('/v1/hubs/recommend'); // may 404
      if (rec && Number.isFinite(rec.lat) && Number.isFinite(rec.lng)) {
        charger[0] = rec.lat;
        charger[1] = rec.lng;
      }
    } catch(_) {}

    try {
      const deals = await apiGet('/v1/deals/nearby'); // may 404
      const d0 = Array.isArray(deals) ? deals[0] : null;
      if (d0 && Number.isFinite(d0.lat) && Number.isFinite(d0.lng)) {
        merch[0] = d0.lat;
        merch[1] = d0.lng;
      }
    } catch(_) {}

    addChargerDot(charger);
    addMerchantDot(merch);
    drawRoute([charger, merch], { dashed:true });
  }

  // Perk card
  const card = document.getElementById('perk-card');
  if (card) {
    // Get merchant data for display
    let merchantName = 'Nearby perk';
    let merchantReward = 'Cheaper during Green Hour';
    let merchantWindow = '2–4pm';
    let merchantDistance = '0.3 mi from charger';

    try {
      const deals = await apiGet('/v1/deals/nearby');
      const d0 = Array.isArray(deals) ? deals[0] : null;
      if (d0) {
        merchantName = d0.name || merchantName;
        merchantReward = d0.reward_text || merchantReward;
        merchantWindow = d0.window || merchantWindow;
        merchantDistance = d0.distance_text || merchantDistance;
      }
    } catch(_) {}

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
      // Switch to charge tab (no import from app.js needed)
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