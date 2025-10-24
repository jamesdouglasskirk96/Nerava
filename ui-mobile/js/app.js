// Main app controller
import { loadDemoState } from './core/demo.js';
import { ensureDemoBanner } from './components/demoBanner.js';
import { apiGet, apiPost } from './core/api.js';
import { ensureMap, addOverlay, clearOverlays, fitBounds, getMap } from './js/core/map.js';
window.Nerava = window.Nerava || {};

// === SSO → prefs → wallet pre-balance → push banner flow ===
function getUser(){ return localStorage.NERAVA_USER || null; }
function setUser(email){ localStorage.NERAVA_USER = email; const b = document.getElementById('auth-badge'); if(b) b.textContent=email; }
function renderSSO(){ if(document.getElementById('sso-overlay')) return;
  const wrap = document.createElement('div'); wrap.id='sso-overlay';
  wrap.style.cssText='position:fixed;inset:0;background:rgba(15,23,42,.72);backdrop-filter:blur(6px);display:flex;align-items:center;justify-content:center;z-index:100000;';
  wrap.innerHTML = `<div id="sso-card" style="width:clamp(320px,90vw,420px);background:#fff;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.25);padding:20px">
    <h2 style="margin:0 0 8px;font:700 18px/1.2 -apple-system,system-ui">Welcome</h2>
    <p style="margin:0 0 12px;color:#64748b">Sign in to set preferences, see wallet, and claim incentives.</p>
    <div class="sso-row">
      <button id="btn-email"  class="sso-btn">Email sign up</button>
      <button id="btn-apple"  class="sso-btn btn-apple"><span>🍎</span><span>Sign in with Apple</span></button>
      <button id="btn-google" class="sso-btn btn-google"><span>G</span><span>Sign in with Google</span></button>
    </div>
    <p style="margin:12px 0 0;color:#94a3b8;font-size:12px">By continuing you agree to the Terms &amp; Privacy.</p>
  </div>`;
  document.body.appendChild(wrap);
  const proceed=(email)=>{
    setUser(email);
    const bal=document.getElementById('wallet-balance'); if(bal) bal.textContent='+$0.00'; // pre-balance
    const e=document.getElementById('prof-email'); if(e) e.textContent=email; // show profile email
    wrap.remove();
    loadPrefs(); loadWallet(); loadBanner(); loadRecommendation();
    triggerDemoPush();
  };
  wrap.querySelector('#btn-apple').onclick  = ()=> proceed('apple_demo@nerava.app');
  wrap.querySelector('#btn-google').onclick = ()=> proceed('google_demo@nerava.app');
  wrap.querySelector('#btn-email').onclick  = ()=>{ const em=prompt('Enter your email:','you@nerava.app'); if(em) proceed(em); };
}
function ensureAuth(){ if(!getUser()){ renderSSO(); return false; } const b=document.getElementById('auth-badge'); if(b) b.textContent=getUser(); return true; }
function triggerDemoPush(){
  if(document.getElementById('demo-push')) return;
  const bar=document.createElement('div'); bar.id='demo-push';
  bar.className='demo-push'; bar.textContent='Recommended by Nerava AI • Cheaper charging nearby — View';
  bar.onclick=()=>{ setTab('explore'); loadRecommendation(); bar.remove(); };
  document.body.appendChild(bar); setTimeout(()=>{ if(bar.parentNode) bar.remove(); },7000);
}

// Placeholder functions for the flow
function loadPrefs(){ /* Load user preferences */ }
function loadWallet(){ /* Load wallet data */ }
function loadBanner(){ /* Load demo banner */ }
function loadRecommendation(){ 
  // Set the badge with brand color + bolt icon
  const tierText = 'Cheaper charging nearby';
  const bolt = `<svg aria-hidden="true" viewBox="0 0 24 24" width="14" height="14" style="margin-right:6px"><path fill="currentColor" d="M13 2 3 14h7l-1 8 10-12h-7l1-8z"/></svg>`;
  const badge = `<span class="ai-badge">${bolt}<span>Recommended by Nerava AI • ${tierText}</span></span>`;
  const hubTier = document.getElementById('hub-tier');
  if (hubTier) hubTier.innerHTML = badge;
  if (typeof capHero === 'function') capHero();
}

// Alias for setActive (legacy compatibility)
function setTab(tab) { setActive(tab); }

// Map initialization function - idempotent and non-recursive
let __mapInstance = null;
function ensureMap(lat=30.4021,lng=-97.7265){
  const afterLayout = () => { try{ __mapInstance && __mapInstance.invalidateSize(false); }catch(_){} };
  if (__mapInstance) {
    try { __mapInstance.setView([lat,lng], Math.max(__mapInstance.getZoom()||14, 14)); } catch(_){}
    requestAnimationFrame(()=>setTimeout(afterLayout, 50));
    return __mapInstance;
  }
  if (!window.L) return null; // Leaflet not loaded yet
  __mapInstance = L.map('map',{ zoomControl:false });
  __mapInstance.setView([lat,lng], 14);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom: 19, attribution: '&copy; OpenStreetMap'
  }).addTo(__mapInstance);
  requestAnimationFrame(()=>setTimeout(afterLayout, 50));
  return __mapInstance;
}
// Back-compat alias
function initMap(lat, lng){ return ensureMap(lat, lng); }

// ---- legacy global exports for non-module callers ----
// Removed exports to avoid "does not provide an export named" errors
if (typeof window !== 'undefined') {
  window.setTab = setTab;
  window.initMap = initMap;
  window.loadRecommendation = loadRecommendation;
  window.loadBanner = loadBanner;
  window.loadWallet = loadWallet;
  window.loadPrefs = loadPrefs;
}

// === Layout helpers ===
const rootStyle = document.documentElement.style;

function setMapInsets({ hasSheet = false, sheetPx = 0 } = {}) {
  // Update CSS vars to push map correctly
  rootStyle.setProperty('--sheet-h', `${sheetPx}px`);
  const mapEl = document.getElementById('chargeMap');
  if (!mapEl) return;
  mapEl.classList.toggle('has-sheet', !!hasSheet);
}

// Scan panel has been permanently removed from HTML

// Tab management
const tabs = ['Explore','Charge','Claim','Wallet','Me'];
const inited = {};

// Handle hash routing
function handleHashRoute() {
  const hash = location.hash;
  if (hash === '#/dev') {
    // Show dev page
    document.getElementById('pageDev')?.classList.remove('hidden');
    document.getElementById('dev-content').innerHTML = '';
    import('./pages/dev.js').then(module => {
      module.mountDev(document.getElementById('dev-content'));
    });
  } else {
    // Hide dev page
    document.getElementById('pageDev')?.classList.add('hidden');
  }
}

function setActive(tab){
  tabs.forEach(n => {
    const on = (n === tab);
    document.getElementById(`tab${n}`)?.classList.toggle('active', on);
    document.getElementById(`page${n}`)?.classList.toggle('hidden', !on);
  });

  // Layout rules per tab
  if (tab === 'Explore') {
    // Only the compact perk sheet is shown; set its approximate height
    const perkSheet = document.getElementById('perkSheet') || document.querySelector('[data-role="perk-sheet"]');
    const h = perkSheet ? Math.min(320, perkSheet.offsetHeight || 320) : 320;
    setMapInsets({ hasSheet: true, sheetPx: h });
    
    // Initialize explore only once, then just invalidate map
    if (!window.__exploreBooted) {
      import('./pages/explore.js').then(module => {
        module.initExplore();
        window.__exploreBooted = true;
      }).catch(() => {});
    } else {
      // Just invalidate map size on tab show
      requestAnimationFrame(() => {
        import('./core/map.js').then(module => {
          module.invalidateMap();
        }).catch(() => {});
      });
    }
  } else if (tab === 'Claim') {
    const claimSheet = document.getElementById('claimSheet') || document.querySelector('[data-role="claim-sheet"]');
    const h = claimSheet ? Math.min(360, claimSheet.offsetHeight || 360) : 360;
    setMapInsets({ hasSheet: true, sheetPx: h });
  } else {
    // Charge, Wallet, Me → no sheet for now; show full map behind header/nav
    setMapInsets({ hasSheet: false, sheetPx: 0 });
  }

  // Hide Scan panel when on Charge (temporary)
  if (tab === 'Charge' && SCAN_TEMP_DISABLED) {
    const scan = document.querySelector('[data-role="scan-panel"]');
    if (scan) scan.classList.add('hidden');
  }

  // Lazy init per page
  if (!inited[tab]) {
    inited[tab] = true;
    const initFn = window[`init${tab}`];
    if (typeof initFn === 'function') initFn();
  }

  // Map repaint on Explore only
  if (tab === 'Explore' && typeof window.repaintMap === 'function') {
    requestAnimationFrame(window.repaintMap);
  }
}

// Wire tab buttons
function wireTabs() {
  document.getElementById('tabExplore')?.addEventListener('click', ()=>setActive('Explore'));
  document.getElementById('tabCharge')?.addEventListener('click',  ()=>setActive('Charge'));
  document.getElementById('tabWallet')?.addEventListener('click',  ()=>setActive('Wallet'));
  document.getElementById('tabMe')?.addEventListener('click',      ()=>setActive('Me'));

  document.getElementById('tabScan')?.addEventListener('click',    ()=> {
    // Open scan modal/sheet if you have it, or route to Claim
    setActive('Claim');
  });
}

// Initialize app
async function initApp() {
  wireTabs();
  
  // Load demo state and show banner if enabled
  await loadDemoState();
  ensureDemoBanner();
  
  // Add keyboard shortcut for dev tab
  document.addEventListener('keydown', (e)=>{ 
    if(e.key==='d' || e.key==='D'){ 
      location.hash='#/dev'; 
    } 
  });
  
  // Handle hash routing
  window.addEventListener('hashchange', handleHashRoute);
  handleHashRoute();
  
  // Set initial tab
  setActive('Explore');
  
  // Add bottom padding to all pages
  const pages = document.querySelectorAll('.page, #pageExplore, #pageCharge, #pageWallet, #pageMe, #pageClaim');
  pages.forEach(p => { 
    p.style.paddingBottom = `calc(84px + env(safe-area-inset-bottom, 12px))`; 
  });
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', async ()=>{ 
  // Derive brand color from logo if present
  try {
    const logo = document.querySelector('#logo, .brand-logo, header .logo, .topbar .logo');
    const root = document.documentElement;
    if (logo && root) {
      const cs = getComputedStyle(logo);
      const c = cs.fill && cs.fill !== 'none' ? cs.fill : (cs.color || '');
      if (c) root.style.setProperty('--brand', c);
    }
  } catch(_) {}

  setTab('Explore');            // now guaranteed defined
  initMap();
  // Gate on SSO; after SSO completes, it calls the loaders again.
  if (typeof ensureAuth === 'function' && !ensureAuth()) return;
  await loadBanner();
  await loadRecommendation();
  await loadWallet();
  await loadPrefs();
});

// Demo autorun keyboard shortcut (Shift+R)
window.addEventListener('keydown', (e)=>{
  if((e.key==='R' || e.key==='r') && e.shiftKey && window.NeravaDemoRunner){
    window.NeravaDemoRunner.runInvestorScript();
  }
});

// Resize handler for map invalidation (debounced)
(function(){
  let t;
  const kick = () => { clearTimeout(t); t=setTimeout(()=>{ try{ ensureMap(); }catch(_){ } }, 120); };
  window.addEventListener('resize', kick, { passive:true });
  window.addEventListener('orientationchange', kick, { passive:true });
})();

// Cap hero images to prevent layout issues
function capHero(){
  const hero = document.querySelector('.perk-hero img, .perk-hero svg');
  if (hero) { hero.removeAttribute('width'); hero.removeAttribute('height'); }
}

// ---- geo helpers ----
const meters = (lat1, lon1, lat2, lon2) => {
  const toRad = d=>d*Math.PI/180, R = 6371000;
  const dlat = toRad(lat2-lat1), dlon = toRad(lon2-lon1);
  const a = Math.sin(dlat/2)**2 + Math.cos(toRad(lat1))*Math.cos(toRad(lat2))*Math.sin(dlon/2)**2;
  return 2*R*Math.asin(Math.sqrt(a));
};
const walkETAmin = (m) => Math.max(1, Math.round(m/1.4/60)); // 1.4 m/s

// Leaflet layers for route/markers
let walkLayer, chargerMarker, merchantMarker;

async function drawWalkingRoute(charger, merchant){
  if(!__mapInstance) ensureMap(charger.lat, charger.lng);
  if(walkLayer){ try{ walkLayer.remove(); }catch(e){} }
  if(chargerMarker){ try{ chargerMarker.remove(); }catch(e){} }
  if(merchantMarker){ try{ merchantMarker.remove(); }catch(e){} }

  // markers
  chargerMarker = L.circleMarker([charger.lat, charger.lng], {radius:6, color:'#0ea5e9'});
  merchantMarker = L.circleMarker([merchant.lat, merchant.lng], {radius:6, color:'#f59e0b'});
  chargerMarker.addTo(__mapInstance); merchantMarker.addTo(__mapInstance);

  // try OSRM pedestrian (best effort; optional)
  let line;
  try{
    const url = `https://router.project-osrm.org/route/v1/foot/${charger.lng},${charger.lat};${merchant.lng},${merchant.lat}?overview=full&geometries=geojson`;
    const r = await fetch(url, { mode:'cors' });
    const j = r.ok ? await r.json() : null;
    const coords = j?.routes?.[0]?.geometry?.coordinates?.map(([x,y])=>[y,x]);
    if(coords && coords.length){ line = L.polyline(coords, {weight:5, opacity:.9}); }
  }catch(_){} // ignore

  // fallback: straight line
  if(!line){ line = L.polyline([[charger.lat,charger.lng],[merchant.lat,merchant.lng]], {dashArray:'6,8', weight:4}); }
  walkLayer = line.addTo(__mapInstance);

  // fit and badge
  const distM = meters(charger.lat, charger.lng, merchant.lat, merchant.lng);
  __mapInstance.fitBounds(L.latLngBounds([[charger.lat,charger.lng],[merchant.lat,merchant.lng]]), { padding:[40,40] });
  showWalkCTA(charger.name||'Charger', merchant.name||'Merchant', distM);
  
  // Show route badge
  const badge = document.getElementById('route-badge');
  if (badge) badge.style.removeProperty('display');
}

function showWalkCTA(chargerName, merchantName, distM){
  let box = document.getElementById('walk-cta');
  if(!box){
    box = document.createElement('div');
    box.id = 'walk-cta'; box.className = 'walk-cta';
    document.getElementById('page-explore')?.prepend(box);
  }
  const eta = walkETAmin(distM);
  box.innerHTML = `Walk to <b>${merchantName}</b> from ${chargerName} • ~${eta} min (${Math.round(distM)}m)
    <button id="btn-start-walk">Start</button>`;
  document.getElementById('btn-start-walk').onclick = ()=> setTab('explore'); // already here; keep focus
}

// --- Dual-zone MVP ---
let dualSession = null;
let geoWatchId = null;
let lastTick = 0;

async function startDualSession(user_id, charger, merchant){
  // hit backend to create a session (flag-gated)
  try{
    const res = await NeravaAPI.apiPost('/v1/dual/start', {
      user_id, charger_id: charger.id, merchant_id: merchant.id,
      charger_radius_m: 40, merchant_radius_m: 100, dwell_threshold_s: 180
    });
    dualSession = { id: res.session_id, charger, merchant };
    drawWalkingRoute(charger, merchant);
    startGeoWatch();
  }catch(e){ console.warn('dual start failed (flag off or server down)', e); }
}

function startGeoWatch(){
  if(geoWatchId) return;
  if(!navigator.geolocation){ console.warn('no geolocation'); return; }
  geoWatchId = navigator.geolocation.watchPosition(pos=>{
    const now = Date.now();
    if(now - lastTick < 12000) return; // throttle 12s
    lastTick = now;

    const p = { lat: pos.coords.latitude, lng: pos.coords.longitude };
    if(dualSession){
      // optimistic front-end verify tick (no server dependency in demo)
      const m1 = meters(p.lat,p.lng, dualSession.charger.lat, dualSession.charger.lng);
      const m2 = meters(p.lat,p.lng, dualSession.merchant.lat, dualSession.merchant.lng);
      // call server (best effort)
      NeravaAPI.apiPost('/v1/dual/tick', {
        session_id: dualSession.id,
        user_pos: p,
        charger_pos: { lat: dualSession.charger.lat, lng: dualSession.charger.lng },
        merchant_pos:{ lat: dualSession.merchant.lat, lng: dualSession.merchant.lng }
      }).then(j=>{
        if(j?.status==='verified'){
          triggerWalletToast('✅ Session verified by location. Reward added.');
        }
      }).catch(()=>{/* ignore in demo */});
    }
  }, err=>console.warn('geo error', err), { enableHighAccuracy:false, maximumAge:15000, timeout:12000 });
}

function triggerWalletToast(msg){
  try{
    const t = document.createElement('div');
    t.style.cssText='position:fixed;left:50%;bottom:calc(var(--tabbar-height) + 18px);transform:translateX(-50%);background:#111;color:#fff;padding:10px 14px;border-radius:12px;z-index:9999;font-weight:700';
    t.textContent = msg; document.body.appendChild(t); setTimeout(()=>t.remove(), 3200);
  }catch(_){}
}

// IMPORTANT: do not call L.map() anywhere else in this file.
// Boot should call initExplore(); do NOT call another initMap().

window.addEventListener('load', async ()=>{
  setTab('explore');
  ensureMap('map'); // Initialize map once
  await loadBanner();
  await loadWallet();
  await loadPrefs();
});

// Export functions for use by other modules
// Removed exports to avoid "does not provide an export named" errors