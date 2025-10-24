import { setTab, ensureMap } from '../app.js';
import { apiGet } from '../core/api.js';

const W_LAT = 30.4025, W_LNG = -97.7258;

export async function initExplore(){
  // Load recommended hub + best merchant
  let hub, merchant;
  try{
    hub = await apiGet('/v1/hubs/recommend', { lat: W_LAT, lng: W_LNG, radius_km: 2 });
  }catch{ hub = null; }
  if(!hub) hub = { lat: W_LAT, lng: W_LNG, name:'Nerava Hub'};

  try{
    const deals = await apiGet('/v1/deals/nearby', { lat: hub.lat, lng: hub.lng, limit: 1 });
    merchant = deals?.items?.[0] || null;
  }catch{ merchant = null; }
  if(!merchant) merchant = { name:'Coffee & Pastry', lat: 30.404, lng:-97.7241, reward_text:'Free coffee with charging', window:'2–4pm', distance_text:'0.3 mi' };

  // Map & route
  if (window.L && document.getElementById('map') && isFinite(hub.lat) && isFinite(merchant.lat)) {
    const m = ensureMap(hub.lat, hub.lng);
    if (m && typeof m.addLayer === 'function') {
      const start = L.latLng(hub.lat, hub.lng);
      const end   = L.latLng(merchant.lat, merchant.lng);
      const line  = L.polyline([start,end], { color: '#3a7bff', weight:4, opacity:.85, dashArray:'6,8' });
      line.addTo(m);
      m.fitBounds(line.getBounds(), { padding: [26,26], maxZoom: 16 });
      L.circleMarker(end,{ radius:7, color:'#3a7bff', weight:3, fill:true, fillColor:'#3a7bff' }).addTo(m);
      window._routeLayer = { line };
    }
  }

  // Perk card
  const card = document.getElementById('perk-card');
  if(card){
    card.innerHTML = `
      <div class="perk-card">
        <div class="ai-chip">⚡ Recommended by Nerava AI</div>
        <div class="perk-body">
          <div class="logo">☕</div>
          <div class="info">
            <h3>${merchant?.name || 'Nearby perk'}</h3>
            <p>${merchant?.reward_text || 'Cheaper during Green Hour'} • ${merchant?.window || '2–4pm'}<br/>
            ${merchant?.distance_text || '0.3 mi from charger'}</p>
          </div>
          <button id="btn-charge-here" class="btn btn-primary">Charge here</button>
        </div>
      </div>
    `;
    document.getElementById('btn-charge-here')?.addEventListener('click',()=> setTab('charge'));
  }

  document.getElementById('btn-view-more')?.addEventListener('click', ()=> alert('List of perks based on your preferences (coming soon)'));
}

// boot when page shown
document.addEventListener('DOMContentLoaded', ()=> initExplore());