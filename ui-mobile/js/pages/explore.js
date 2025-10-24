import { ensureMap, drawWalkingRoute } from '../app.js';
import { apiGet } from '../core/api.js';

export async function initExplore() {
  const map = ensureMap();
  if (!map) return;
  
  // fetch recommend & deals (soft-null allowed)
  const rec   = (await apiGet('/v1/hubs/recommend', { lat:30.4025, lng:-97.7258, radius_km:2 })) || {};
  const deals = (await apiGet('/v1/deals/nearby',    { lat:30.4025, lng:-97.7258 })) || { items:[] };
  
  // fallback demo points:
  const charger = rec.lat ? { lat: rec.lat, lng: rec.lng } : { lat: 30.4029, lng: -97.7255 };
  const merchant = deals.items?.[0]?.pos || { lat: 30.4039, lng: -97.7242 };
  drawWalkingRoute(map, charger, merchant);

  // Perk card
  const card = document.getElementById('perk-card');
  if (card) {
    card.innerHTML = `
      <div class="perk-card">
        <div class="ai-chip">⚡ Recommended by Nerava AI</div>
        <div class="perk-body">
          <div class="logo">☕</div>
          <div class="info">
            <h3>${deals.items?.[0]?.name || 'Nearby perk'}</h3>
            <p>${deals.items?.[0]?.reward_text || 'Cheaper during Green Hour'} • ${deals.items?.[0]?.window || '2–4pm'}<br/>
            ${deals.items?.[0]?.distance_text || '0.3 mi from charger'}</p>
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