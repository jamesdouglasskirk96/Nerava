import { ensureMap, drawWalkingRoute } from '../app.js';
import { apiGet } from '../core/api.js';

export async function initExplore() {
  const map = ensureMap(); // creates or reuses
  // Defaults if APIs 404
  let hub = { lat: 30.4029, lng: -97.7247 };
  let merchant = { lat: 30.4046, lng: -97.7241 };

  try {
    const rec = await apiGet('/v1/hubs/recommend'); // may 404
    if (rec && Number.isFinite(rec.lat) && Number.isFinite(rec.lng)) {
      hub = { lat: rec.lat, lng: rec.lng };
    }
  } catch(_) {}

  try {
    const deals = await apiGet('/v1/deals/nearby'); // may 404
    const d0 = Array.isArray(deals) ? deals[0] : null;
    if (d0 && Number.isFinite(d0.lat) && Number.isFinite(d0.lng)) {
      merchant = { lat: d0.lat, lng: d0.lng };
    }
  } catch(_) {}

  // Only draw when both are valid
  const ok = p => p && Number.isFinite(p.lat) && Number.isFinite(p.lng);
  if (ok(hub) && ok(merchant)) drawWalkingRoute(hub, merchant);

  // Perk card
  const card = document.getElementById('perk-card');
  if (card) {
    card.innerHTML = `
      <div class="perk-card">
        <div class="ai-chip">⚡ Recommended by Nerava AI</div>
        <div class="perk-body">
          <div class="logo">☕</div>
          <div class="info">
            <h3>${merchant.name || 'Nearby perk'}</h3>
            <p>${merchant.reward_text || 'Cheaper during Green Hour'} • ${merchant.window || '2–4pm'}<br/>
            ${merchant.distance_text || '0.3 mi from charger'}</p>
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