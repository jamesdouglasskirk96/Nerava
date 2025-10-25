import { apiGet } from '../core/api.js';
import { ensureMap } from '../app.js';
import { setTab } from '../app.js';

const $ = (s, r=document) => r.querySelector(s);

export async function initExplore(){
  const map = await ensureMap();          // uses existing map initializer
  setTimeout(() => map.invalidateSize(), 0);

  // Fit to any existing route bounds if available; otherwise default city view
  if (window.lastBounds){
    map.fitBounds(window.lastBounds, { padding:[20,20] });
  } else {
    map.setView([30.2672, -97.7431], 14);
  }

  // Populate perk card with fallback data if API 404s
  let hub = null, deal = null;
  try { hub  = await apiGet('/v1/hubs/recommend'); } catch(_){}
  try { deal = await apiGet('/v1/deals/nearby');    } catch(_){}

  const name  = deal?.merchant?.name   ?? 'Coffee & Pastry';
  const addr  = deal?.merchant?.address?? '310 E 5th St, Austin, TX';
  const text  = deal?.summary ?? 'Free coffee 2–4pm · 3 min walk from charger';
  const logo  = deal?.merchant?.logo   ?? '☕️';

  $('#perkName').textContent  = name;
  $('#perkAddr').textContent  = addr;
  $('#perkDetails').textContent = text;
  $('#perkLogo').textContent  = ''; 
  $('#perkLogo').appendChild(typeof logo === 'string' ? document.createTextNode(logo) : logo);

  // Button actions
  $('#btnChargeHere').onclick = () => setTab('charge');
  $('#btnViewMore').onclick   = () => openPerkListModal?.() || alert('Coming soon: list of perks');

  // Make sure the map card never overlaps content
  const card = $('.map-card');
  if (card){ card.style.zIndex = 0; }
}