function baseUrl(){ return (localStorage.NERAVA_URL || location.origin.replace(/\/$/, '')); }
function toUrl(path){
  if(/^https?:\/\//i.test(path)) return path;
  if(path.startsWith('/')) return baseUrl()+path;
  return baseUrl()+'/'+path.replace(/^\/+/, '');
}
async function _req(path,{method='GET',body,headers={}}={}){
  const r=await fetch(toUrl(path),{method,headers:{'Accept':'application/json',...(body?{'Content-Type':'application/json'}:{}),...headers},body:body?JSON.stringify(body):undefined}).catch(() => null);
  if (!r || !r.ok) {
    // Soft 404/Network: return null; caller will use fallbacks.
    if (r && r.status && r.status !== 404) console.debug('apiGet non-OK', r.status, path);
    return null;
  }
  // Some 204/empty responses: return null
  if (r.status === 204) return null;
  const ct=r.headers.get('content-type')||''; return ct.includes('application/json')?r.json():r.text();
}
export async function apiGet(p,h={}){ return _req(p,{method:'GET',headers:h}); }
export async function apiPost(p,b={},h={}){ return _req(p,{method:'POST',body:b,headers:h}); }
if(typeof window!=='undefined'){ window.NeravaAPI=window.NeravaAPI||{}; window.NeravaAPI.apiGet=apiGet; window.NeravaAPI.apiPost=apiPost; }
export default { apiGet, apiPost };