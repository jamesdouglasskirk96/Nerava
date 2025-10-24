import { ensureMap, addOverlay, clearOverlays, fitBounds, getMap } from '../core/map.js';
import { apiGet } from '../core/api.js';

export async function initExplore() {
  const map = ensureMap('map', { zoom: 16 });

  // Fetch with safe fallbacks
  let rec = null, deals = [];
  try { rec = await apiGet('/v1/hubs/recommend'); } catch {}
  try { deals = await apiGet('/v1/deals/nearby'); } catch {}

  // Fallback data if 404 or null
  rec = rec || { lat: 30.4028, lng: -97.7240, name: 'Nerava Hub' };
  const perk = (deals && deals[0]) || {
    lat: 30.4036, lng: -97.7249, name: 'Neiman Marcus Café', reward_cents: 300
  };

  // Draw markers/route safely
  clearOverlays();
  if (window.L && map) {
    const start = window.L.circleMarker([rec.lat, rec.lng], { radius: 7, color: '#2b6cb0' });
    const end   = window.L.circleMarker([perk.lat, perk.lng], { radius: 7, color: '#2b6cb0', fillOpacity: 1 });

    addOverlay(start);
    addOverlay(end);

    const line = window.L.polyline([[rec.lat, rec.lng],[perk.lat, perk.lng]], { dashArray: '6,6', color:'#2b6cb0', weight:4 });
    addOverlay(line);

    fitBounds(window.L.latLngBounds([ [rec.lat,rec.lng], [perk.lat,perk.lng] ]));
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
            <h3>${perk.name || 'Nearby perk'}</h3>
            <p>${perk.reward_text || 'Cheaper during Green Hour'} • ${perk.window || '2–4pm'}<br/>
            ${perk.distance_text || '0.3 mi from charger'}</p>
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