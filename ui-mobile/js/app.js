// Main app controller
import { loadDemoState } from './core/demo.js';
import { ensureDemoBanner } from './components/demoBanner.js';
import { apiGet, apiPost } from './core/api.js';
import { ensureMap, drawRoute, clearRoute, getMap } from './core/map.js';

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

// setTab now defined as export function below

// ---- legacy global exports for non-module callers ----
// Removed exports to avoid "does not provide an export named" errors
if (typeof window !== 'undefined') {
  window.setTab = setTab;
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

export function setTab(tab){
  console.log('setTab called with:', tab);
  document.querySelectorAll('.page').forEach(p=>p.classList.toggle('active', p.id==='page-'+tab));
  document.querySelectorAll('.tabbar .tab').forEach(t=>t.classList.toggle('active', t.dataset.tab===tab));
  if(tab==='explore') ensureMap();
  if(tab==='activity') initActivity();
  if(tab==='earn') initEarn();
  if(tab==='wallet') {
    console.log('Calling initWallet...');
    initWallet();
  }
  if(tab==='profile') {
    console.log('Calling initMe...');
    initMe();
  }
}

// Wire tab buttons and FAB
document.querySelectorAll('.tabbar .tab').forEach(t=>{
  t.addEventListener('click', () => setTab(t.dataset.tab));
});

document.getElementById('fab-earn')?.addEventListener('click', ()=> {
  // open earn flow
  setTab('earn');
});

// Initialize app
async function initApp() {
  
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
  setTab('explore');
  
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

// Map resize handling now managed by js/core/map.js module

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

// Make map functions available globally
window.ensureMap = ensureMap;
window.drawRoute = drawRoute;
window.clearRoute = clearRoute;
window.getMap = getMap;

// Draw walking route from user to charger
async function drawWalkingRoute(userLocation, charger, options = {}) {
  try {
    console.log('drawWalkingRoute called with:', { userLocation, charger });
    
    const map = await ensureMap();
    console.log('Map from ensureMap:', map);
    
    if (!map) {
      console.error('No map instance available');
      return;
    }
    
    // Clear any existing routes first
    clearRoute();
    
    // Create route points from user to charger
    const routePoints = [
      [userLocation.lat, userLocation.lng],
      [charger.lat, charger.lng]
    ];
    
    console.log('Drawing route points:', routePoints);
    
    // Use the drawRoute function from map module
    drawRoute(routePoints);
    
  } catch (error) {
    console.error('Failed to draw walking route:', error);
  }
}

// Make drawWalkingRoute available globally
window.drawWalkingRoute = drawWalkingRoute;

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
  // Start with explore tab by default
  setTab('explore');
  // lazy import to avoid cyclic loads
  const { initExplore } = await import('/app/js/pages/explore.js');
  initExplore();
  await loadBanner();
  await loadWallet();
  await loadPrefs();
});

// Initialize activity page when tab is switched
async function initActivity() {
  const activityEl = document.getElementById('page-activity');
  if (activityEl && !activityEl.dataset.initialized) {
    const { initActivityPage } = await import('/app/js/pages/activity.js');
    await initActivityPage(activityEl);
    activityEl.dataset.initialized = 'true';
  }
}

// Initialize earn page when tab is switched
async function initEarn() {
  const earnEl = document.getElementById('page-earn');
  if (earnEl && !earnEl.dataset.initialized) {
    const { initEarnPage } = await import('/app/js/pages/earn.js');
    await initEarnPage(earnEl);
    earnEl.dataset.initialized = 'true';
  }
}

// Initialize wallet page when tab is switched
async function initWallet() {
  const walletEl = document.getElementById('page-wallet');
  console.log('initWallet called, walletEl:', walletEl);
  if (walletEl && !walletEl.dataset.initialized) {
    console.log('Initializing wallet page...');
    const { initWalletPage } = await import('/app/js/pages/wallet.js');
    await initWalletPage(walletEl);
    walletEl.dataset.initialized = 'true';
    console.log('Wallet page initialized');
  }
}

// Initialize me page when tab is switched
async function initMe() {
  const meEl = document.getElementById('page-profile');
  console.log('initMe called, meEl:', meEl);
  if (meEl && !meEl.dataset.initialized) {
    console.log('Initializing me page...');
    // Remove hidden class first
    meEl.classList.remove('hidden');
    const { initMePage } = await import('/app/js/pages/me.js');
    await initMePage(meEl);
    meEl.dataset.initialized = 'true';
    console.log('Me page initialized');
  }
}

// Export functions for use by other modules
// Removed exports to avoid "does not provide an export named" errors