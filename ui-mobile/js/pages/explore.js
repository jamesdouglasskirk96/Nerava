import { ensureMap, drawWalkingRoute } from '../core/map.js';
import { apiGet } from '../core/api.js';

const W_LAT = 30.4025, W_LNG = -97.7258;
const FALLBACK_REC = { lat: W_LAT, lng: W_LNG, name: 'Nerava Hub' };
const FALLBACK_DEAL = { lat: 30.404, lng: -97.7241, name: 'Coffee & Pastry', reward_text: 'Free coffee with charging', window: '2–4pm', distance_text: '0.3 mi' };

export async function initExplore() {
  // Ensure map exists
  const map = ensureMap('map');
  
  // Fetch recommendations and deals with fallbacks
  const rec = await apiGet('/v1/hubs/recommend') || FALLBACK_REC;
  const deal = await apiGet('/v1/deals/nearby') || FALLBACK_DEAL;
  
  // Guard all undefined fields
  const recLat = rec?.lat || W_LAT;
  const recLng = rec?.lng || W_LNG;
  const dealLat = deal?.lat || 30.404;
  const dealLng = deal?.lng || -97.7241;
  
  // Draw walking route if we have valid coordinates
  if (window.L && map && isFinite(recLat) && isFinite(recLng) && isFinite(dealLat) && isFinite(dealLng)) {
    drawWalkingRoute(
      { lat: recLat, lng: recLng },
      { lat: dealLat, lng: dealLng }
    );
  }

  // Perk card
  const card = document.getElementById('perk-card');
  if (card) {
    card.innerHTML = `
      <div class="perk-card">
        <div class="ai-chip">⚡ Recommended by Nerava AI</div>
        <div class="perk-body">
          <div class="logo">☕</div>
          <div class="info">
            <h3>${deal?.name || 'Nearby perk'}</h3>
            <p>${deal?.reward_text || 'Cheaper during Green Hour'} • ${deal?.window || '2–4pm'}<br/>
            ${deal?.distance_text || '0.3 mi from charger'}</p>
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