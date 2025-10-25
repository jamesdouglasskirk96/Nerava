import { apiGet } from '../core/api.js';
import { ensureMap, drawRoute } from '../core/map.js';

export async function initExplore(){
  // Map in rounded card
  const map = ensureMap([30.4025,-97.7258], 14);
  if(!map) return;

  // Try live APIs; fall back to demo coords on 404
  let hub = null, deal = null;
  try { hub = await apiGet('/v1/hubs/recommend'); } catch {}
  try { deal = await apiGet('/v1/deals/nearby'); } catch {}

  // Fallback demo data (domain → coffee)
  const start = hub?.lat && hub?.lng ? [hub.lat, hub.lng] : [30.4029,-97.7262];      // Charger
  const end   = deal?.lat && deal?.lng ? [deal.lat, deal.lng] : [30.4021,-97.7242];  // Merchant

  drawRoute([start, end]);

  // Fill the perk card (AI chip + CTA)
  const name = deal?.merchant_name || 'Coffee & Pastry';
  const when = deal?.window_text || '2–4pm';
  const reward = deal?.reward_text || 'Free coffee w/ charging';
  const card = document.getElementById('perkCard');
  if(card){
    card.querySelector('.perk__name').textContent = name;
    card.querySelector('.perk__desc').textContent = `${reward} • ${when}`;
    card.querySelector('.perk__cta').onclick = () => document.querySelector('[data-tab="charge"]')?.click();
  }
}