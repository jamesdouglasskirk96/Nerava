// Removed old _req function - using new implementation below
const BASE = localStorage.NERAVA_URL || location.origin;
async function _req(path, opts={}){
  const r = await fetch(BASE + path, { headers:{Accept:'application/json'}, ...opts });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}
export const apiGet = (path, params) => {
  const url = new URL(BASE + path);
  Object.entries(params || {}).forEach(([k,v])=>url.searchParams.set(k,v));
  return _req(url.pathname + url.search);
};
export async function apiPost(p,b={},h={}){ return _req(p,{method:'POST',body:b,headers:h}); }
if(typeof window!=='undefined'){ window.NeravaAPI=window.NeravaAPI||{}; window.NeravaAPI.apiGet=apiGet; window.NeravaAPI.apiPost=apiPost; }
export default { apiGet, apiPost };