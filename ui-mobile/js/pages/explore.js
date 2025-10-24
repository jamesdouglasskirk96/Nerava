import { apiGet } from '../core/api.js';

const $ = (s)=>document.querySelector(s);
const fallbackHub = { id:'hub_demo', name:'Nerava Hub', lat:30.4025, lng:-97.7258 };
const fallbackMerchant = { id:'m_starbucks', name:'Starbucks', reward:'Free tall coffee', window:'2–4pm', dist_mi:0.3, lat:30.4032, lng:-97.7241, logo:'☕️' };

export async function initExplore(){
  const root = document.getElementById('page-explore'); if(!root) return;
  // 1) Recommendation (hub) near user
  let hub = null;
  try{
    const r = await apiGet('/v1/hubs/recommend', { lat:30.4025, lng:-97.7258, radius_km:2, user_id:localStorage.NERAVA_USER||'demo@nerava.app' });
    hub = r && r.lat && r.lng ? r : null;
  }catch(_){}; if (!hub) hub = fallbackHub;

  // 2) Nearest merchant perk near that hub (simple heuristic / fallback)
  let perk = null;
  try{
    const d = await apiGet('/v1/deals/nearest', { lat:hub.lat, lng:hub.lng, limit:1 });
    const m = (d?.items||[])[0];
    if (m) perk = { id:m.id, name:m.name, reward:m.reward, window:m.window, dist_mi: m.dist_mi ?? 0.2, lat:m.lat, lng:m.lng, logo: m.logo || '☕️' };
  }catch(_){}
  if (!perk) perk = fallbackMerchant;

  // 3) Draw route + ETA
  if (window.drawWalkingRoute) window.drawWalkingRoute({lat:hub.lat,lng:hub.lng},{lat:perk.lat,lng:perk.lng}, perk.logo);

  // 4) Fill perk card
  $('#perkName').textContent = perk.name;
  $('#perkMeta').textContent = `${perk.reward} • ${perk.window}`;
  $('#perkDist').textContent = `${perk.dist_mi} mi from charger`;
  $('#perkLogo').textContent = perk.logo || '🏪';

  // 5) Buttons
  $('#btnChargeHere').onclick = ()=> {
    // optional: start dual-radius session (if flag on)
    if (window.startDualSession) window.startDualSession({hub, merchant:perk});
    const tabBtn = document.querySelector('.tabbar .tab[data-tab="charge"]'); if (tabBtn) tabBtn.click();
  };
  $('#btnViewMore').onclick = ()=> {
    alert('Showing all perks nearby based on your preferences. (List UI can be filled as a follow-up)');
  };
}