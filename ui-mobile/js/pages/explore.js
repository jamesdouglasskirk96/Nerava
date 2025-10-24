// Explore page logic
import { apiGet, apiPost } from '../core/api.js';

const USER = (localStorage.NERAVA_USER || 'demo@nerava.app');

function htm(str){ const d=document.createElement('div'); d.innerHTML=str.trim(); return d.firstElementChild; }
function money(c){ return `+$${(Number(c||0)/100).toFixed(2)}`; }

export async function initExplore(){
  const root = document.getElementById('page-explore');
  if(!root) return;

  // 1) Fetch recommendation (hub) and best merchant
  let hub=null, merch=null;
  try{
    const lat=30.4025,lng=-97.7258;
    const rec = await apiGet('/v1/hubs/recommend', { lat, lng, radius_km: 2, user_id: USER });
    hub = { lat: rec?.lat ?? lat, lng: rec?.lng ?? lng, name: rec?.name || 'Nerava Hub' };

    // simple merchant pick: first from /v1/deals/nearby or fallback
    const deals = await apiGet('/v1/deals/nearby', { lat, lng, radius_km:2 }).catch(()=>({ items:[] }));
    const d = deals?.items?.[0] || {};
    merch = {
      id: d.id || 'm_local',
      name: d.name || 'Coffee & Pastry',
      logo: d.logo || '/app/img/coffee.png',
      reward_cents: d.reward_cents ?? 300,
      window_text: d.window_text || '2–4pm',
      lat: d.lat ?? (hub.lat + 0.0012),
      lng: d.lng ?? (hub.lng + 0.0010)
    };
  }catch(_){
    // fallback entirely
    hub = hub || { lat:30.4025, lng:-97.7258, name:'Nerava Hub' };
    merch = merch || { id:'m_fallback', name:'Coffee & Pastry', logo:'/app/img/coffee.png', reward_cents:300, window_text:'2–4pm', lat:30.4037, lng:-97.7248 };
  }

  // 2) Draw walking route + ETA badge
  if(window.drawWalkingRoute) window.drawWalkingRoute(hub, merch);

  // 3) Render Nearby Perk card
  const card = document.getElementById('nearby-perk');
  if(card){
    const badge = `<span class="ai-badge"><span aria-hidden="true">⚡</span>Recommended by Nerava AI</span>`;
    card.innerHTML = `
      <div class="row brand">
        <div style="display:flex;align-items:center;gap:10px">
          <img src="${merch.logo}" alt="${merch.name} logo" />
          <div>
            <div style="font-weight:800">${merch.name}</div>
            <div class="meta">${merch.window_text}</div>
          </div>
        </div>
        ${badge}
      </div>
      <div class="meta" style="margin-top:10px;">Reward: <strong>${money(merch.reward_cents)}</strong></div>
      <div class="row" style="margin-top:12px;">
        <button id="btn-charge-here" class="btn-primary">Charge here</button>
        <button id="btn-details" class="btn-secondary">Details</button>
      </div>
    `;
    card.classList.remove('hidden');

    // "Charge here" → start verification flow (if API exists) or switch to Charge tab
    document.getElementById('btn-charge-here')?.addEventListener('click', async ()=>{
      try{
        // optional: start dual session if available
        await apiPost('/v1/dual/start', {
          user_id: USER,
          charger_pos: hub, merchant_pos: merch,
          charger_id: 'hub_best', merchant_id: merch.id,
          charger_radius_m: 40, merchant_radius_m: 100, dwell_threshold_s: 60,
        }).catch(()=>{});
      }catch(_){}
      // Switch to Charge tab
      const btn = document.querySelector('.tabbar .tab[data-tab="charge"]');
      btn?.click();
    });
  }

  // 4) View more → simple list (preferences-aware if backend provides; fallback)
  document.getElementById('btn-view-more')?.addEventListener('click', async ()=>{
    const lat=hub.lat, lng=hub.lng;
    const list = await apiGet('/v1/deals/nearby', { lat, lng, radius_km:5 }).catch(()=>({items:[]}));
    const items = list?.items?.length ? list.items : [merch];
    const modal = htm(`<dialog class="sheet" style="padding:0;max-height:78vh;"></dialog>`);
    const inner = document.createElement('div');
    inner.style.padding = '14px';
    inner.innerHTML = items.map(x => `
      <div style="display:flex;align-items:center;gap:12px;padding:10px 4px;border-bottom:1px solid #eee">
        <img src="${x.logo || merch.logo}" alt="" style="width:40px;height:40px;border-radius:8px;object-fit:cover"/>
        <div style="flex:1">
          <div style="font-weight:700">${x.name || merch.name}</div>
          <div class="meta">Reward ${money(x.reward_cents ?? merch.reward_cents)} · ${x.window_text || merch.window_text}</div>
        </div>
        <button class="btn-secondary" data-mid="${x.id || 'm'}">Select</button>
      </div>
    `).join('');
    modal.appendChild(inner);
    document.body.appendChild(modal);
    modal.showModal?.();

    modal.addEventListener('click', (e)=>{ if(e.target===modal) modal.close(); });
    modal.addEventListener('close', ()=> modal.remove());
  });
}

// Export for app.js to call
window.Nerava = window.Nerava || {};
window.Nerava.pages = window.Nerava.pages || {};
window.Nerava.pages.explore = { init: initExplore };