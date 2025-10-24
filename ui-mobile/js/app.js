// Main app controller
import { loadDemoState } from './core/demo.js';
import { ensureDemoBanner } from './components/demoBanner.js';
import { apiGet, apiPost } from './core/api.js';
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
}

// Alias for setActive (legacy compatibility)
function setTab(tab) { setActive(tab); }

// Map initialization function - idempotent and non-recursive
let __mapInstance = null;
function ensureMap(lat=30.4021,lng=-97.7265){
  if (__mapInstance) {
    try { __mapInstance.setView([lat,lng], Math.max(__mapInstance.getZoom()||14, 14)); } catch(_) {}
    // fix tiles if container size changed
    setTimeout(()=>{ try{ __mapInstance.invalidateSize(false); }catch(_){ } }, 60);
    return __mapInstance;
  }
  if (!window.L) return null; // Leaflet not loaded yet
  __mapInstance = L.map('map',{ zoomControl:false });
  __mapInstance.setView([lat,lng], 14);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom: 19, attribution: '&copy; OpenStreetMap'
  }).addTo(__mapInstance);
  // small delay to let CSS layout
  setTimeout(()=>{ try{ __mapInstance.invalidateSize(false); }catch(_){ } }, 60);
  return __mapInstance;
}
// Back-compat alias
function initMap(lat, lng){ return ensureMap(lat, lng); }

// ---- legacy global exports for non-module callers ----
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
    // Invalidate map when switching to Explore
    try { ensureMap(); } catch(_) {}
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
  let t; window.addEventListener('resize', ()=>{ clearTimeout(t); t = setTimeout(()=>{ try{ ensureMap(); }catch(_){ } }, 120); }, { passive:true });
})();