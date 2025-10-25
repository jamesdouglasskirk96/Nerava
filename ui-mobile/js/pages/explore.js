import { ensureMap } from '../app.js';
import { apiGet } from '../core/api.js';

export async function initExplore(){
  const map = ensureMap();
  if(!map) return;

  // best-effort API (404 tolerated)
  let rec=null, deal=null;
  try{ rec = await apiGet('/v1/hubs/recommend'); }catch{}
  try{ deal = await apiGet('/v1/deals/nearby'); }catch{}

  // fallback demo coords if API missing
  const a = [30.4025, -97.7258], b = [30.2669, -97.7428]; // demo north→downtown
  const start = rec?.lat ? [rec.lat, rec.lng] : a;
  const end   = deal?.lat ? [deal.lat, deal.lng] : b;

  // draw demo line
  const pts = [start, end];
  const route = L.polyline(pts, {color:'#4A72F5', opacity:0.7, weight:6, dashArray:'6,8'});
  route.addTo(map);
  map.fitBounds(route.getBounds(), { padding:[30,30], maxZoom:15 });
}