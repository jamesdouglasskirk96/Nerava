// Main app controller
// API base URL is now determined dynamically in api.js based on environment
// No need to set localStorage.NERAVA_URL unless explicitly overriding

import { loadDemoState } from './core/demo.js';
import { apiGet, apiPost } from './core/api.js';
import { ensureMap, drawRoute, clearRoute, getMap } from './core/map.js';

// Import magic-link auth functions
let apiRequestMagicLink, apiVerifyMagicLink;

window.Nerava = window.Nerava || {};

// Toast helper function
function showToast(message) {
  const toast = document.createElement('div');
  toast.style.cssText = 'position:fixed;left:50%;bottom:100px;transform:translateX(-50%);background:#111;color:#fff;padding:10px 14px;border-radius:12px;z-index:9999;font-weight:700';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => { toast.style.opacity = 1; }, 10);
  setTimeout(() => { toast.style.opacity = 0; toast.addEventListener('transitionend', () => toast.remove()); }, 3000);
}

// === Magic-link auth flow ===
function getUser(){ return localStorage.NERAVA_USER || null; }
function setUser(email){ localStorage.NERAVA_USER = email; const b = document.getElementById('auth-badge'); if(b) b.textContent=email; }

// Render magic-link email-only auth UI
function renderMagicLinkAuth(){ 
  if(document.getElementById('sso-overlay')) return;
  
  const wrap = document.createElement('div'); 
  wrap.id='sso-overlay';
  wrap.style.cssText='position:fixed;inset:0;background:rgba(15,23,42,.72);backdrop-filter:blur(6px);display:flex;align-items:center;justify-content:center;z-index:100000;';
  
  wrap.innerHTML = `<div id="sso-card" style="width:clamp(320px,90vw,420px);background:#fff;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.25);padding:24px">
    <h2 style="margin:0 0 8px;font:700 20px/1.2 -apple-system,system-ui">Sign in to Nerava</h2>
    <p style="margin:0 0 20px;color:#64748b;font-size:14px">Enter your email and we'll send you a magic link to sign in.</p>
    
    <form id="magic-link-form" style="margin-bottom:16px">
      <input 
        type="email" 
        id="magic-email-input" 
        placeholder="you@example.com" 
        required
        autocomplete="email"
        style="width:100%;padding:12px;border:1px solid #e2e8f0;border-radius:8px;font-size:16px;margin-bottom:12px;box-sizing:border-box"
      />
      <button 
        type="submit" 
        id="magic-link-submit"
        style="width:100%;padding:12px;background:#1e40af;color:#fff;border:none;border-radius:8px;font-weight:600;font-size:16px;cursor:pointer"
      >Send Magic Link</button>
    </form>
    
    <div id="magic-link-success" style="display:none;text-align:center;padding:20px 0">
      <div style="font-size:48px;margin-bottom:12px">✉️</div>
      <h3 style="margin:0 0 8px;font:600 18px/1.2 -apple-system,system-ui">Check your email</h3>
      <p style="margin:0 0 16px;color:#64748b;font-size:14px">We've sent a magic link to <strong id="sent-email"></strong></p>
      <p style="margin:0;color:#94a3b8;font-size:12px">Click the link in your email to sign in. It expires in 15 minutes.</p>
      <p id="dev-mode-notice" style="margin-top:12px;padding:12px;background:#fef3c7;border-radius:8px;color:#92400e;font-size:12px;display:none">
        <strong>Dev Mode:</strong> Check backend console for magic link URL.
      </p>
      <button 
        id="magic-link-back"
        style="margin-top:16px;padding:8px 16px;background:transparent;color:#64748b;border:1px solid #e2e8f0;border-radius:6px;font-size:14px;cursor:pointer"
      >Back</button>
    </div>
    
    <div id="magic-link-error" style="display:none;padding:12px;background:#fee2e2;border-radius:8px;color:#dc2626;font-size:14px;margin-bottom:16px"></div>
    
    <p style="margin:16px 0 0;color:#94a3b8;font-size:12px;text-align:center">By continuing you agree to the Terms &amp; Privacy.</p>
  </div>`;
  
  document.body.appendChild(wrap);
  
  const form = wrap.querySelector('#magic-link-form');
  const emailInput = wrap.querySelector('#magic-email-input');
  const submitBtn = wrap.querySelector('#magic-link-submit');
  const successDiv = wrap.querySelector('#magic-link-success');
  const errorDiv = wrap.querySelector('#magic-link-error');
  const sentEmailSpan = wrap.querySelector('#sent-email');
  const backBtn = wrap.querySelector('#magic-link-back');
  
  // Show dev mode notice if on localhost
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    wrap.querySelector('#dev-mode-notice').style.display = 'block';
  }
  
  form.onsubmit = async (e) => {
    e.preventDefault();
    
    const email = emailInput.value.trim().toLowerCase();
    if (!email) return;
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending...';
    errorDiv.style.display = 'none';
    
    try {
      console.log('[Auth][MagicLink] Requesting magic link for:', email);
      
      const { apiRequestMagicLink } = await import('./core/api.js');
      await apiRequestMagicLink(email);
      
      // Show success state
      form.style.display = 'none';
      sentEmailSpan.textContent = email;
      successDiv.style.display = 'block';
      
      console.log('[Auth][MagicLink] Magic link request successful');
    } catch (err) {
      console.error('[Auth][MagicLink] Request failed:', err);
      errorDiv.textContent = err.message || 'Failed to send magic link. Please try again.';
      errorDiv.style.display = 'block';
      submitBtn.disabled = false;
      submitBtn.textContent = 'Send Magic Link';
    }
  };
  
  backBtn.onclick = () => {
    successDiv.style.display = 'none';
    form.style.display = 'block';
    emailInput.value = '';
  };
  
  // Focus email input
  setTimeout(() => emailInput.focus(), 100);
}

// Legacy renderSSO for backward compatibility (fallback)
function renderSSO() {
  renderMagicLinkAuth();
}

function ensureAuth(){ 
  if(!getUser()){ 
    renderMagicLinkAuth(); 
    return false; 
  } 
  const b=document.getElementById('auth-badge'); 
  if(b) b.textContent=getUser(); 
  return true; 
}
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
  
  // Handle Smartcar callback - redirect to profile tab
  if (hash.includes('#profile') || hash.includes('vehicle=connected') || hash.includes('error=')) {
    const params = new URLSearchParams(hash.split('?')[1] || '');
    const vehicle = params.get('vehicle');
    const error = params.get('error');
    
    // Set profile tab
    if (typeof setTab === 'function') {
      setTab('profile');
    } else {
      // Fallback: trigger tab click
      const profileTab = document.querySelector('[data-tab="profile"]');
      if (profileTab) {
        profileTab.click();
      }
    }
    
    // The profile page will handle the query params
    return;
  }
  
  // Handle magic-link callback
  if (hash.startsWith('#/auth/magic')) {
    const params = new URLSearchParams(hash.split('?')[1] || '');
    const token = params.get('token');
    
    if (token) {
      console.log('[Auth][MagicLink] Processing magic link callback');
      
      // Import and verify token
      import('./core/api.js').then(async ({ apiVerifyMagicLink, apiMe }) => {
        try {
          await apiVerifyMagicLink(token);
          
          // Get user info to set in localStorage
          const user = await apiMe();
          if (user && user.email) {
            setUser(user.email);
            console.log('[Auth][MagicLink] Session created for:', user.email);
          }
          
          // Navigate to Wallet tab
          location.hash = '#/wallet';
          window.location.reload();
        } catch (err) {
          console.error('[Auth][MagicLink] Verification failed:', err);
          
          // Show error state
          const wrap = document.createElement('div');
          wrap.id = 'magic-link-error';
          wrap.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,.92);backdrop-filter:blur(6px);display:flex;align-items:center;justify-content:center;z-index:100000;';
          wrap.innerHTML = `<div style="width:clamp(320px,90vw,420px);background:#fff;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.25);padding:24px;text-align:center">
            <h2 style="margin:0 0 12px;font:700 18px/1.2 -apple-system,system-ui;color:#dc2626">Link Expired or Invalid</h2>
            <p style="margin:0 0 20px;color:#64748b">This magic link has expired or is invalid. Please request a new one.</p>
            <button id="retry-magic-link" style="width:100%;padding:12px;background:#1e40af;color:#fff;border:none;border-radius:8px;font-weight:600;cursor:pointer">Request New Link</button>
          </div>`;
          document.body.appendChild(wrap);
          
          wrap.querySelector('#retry-magic-link').onclick = () => {
            wrap.remove();
            location.hash = '#/';
            renderMagicLinkAuth();
          };
        }
      });
      
      return;
    }
  }
  
  // Handle show code page
  if (hash.startsWith('#/code')) {
    const params = new URLSearchParams(hash.split('?')[1] || '');
    const merchantId = params.get('merchant_id');
    
    if (merchantId) {
      document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
        p.style.display = 'none';
      });
      
      const showCodePage = document.getElementById('page-show-code');
      if (showCodePage) {
        showCodePage.style.display = 'block';
        showCodePage.classList.add('active');
        
        import('./pages/showCode.js').then(module => {
          module.initShowCode({ merchant_id: merchantId });
        });
      }
      return;
    }
  }
  
  // Handle Earn page
  if (hash.startsWith('#/earn')) {
    const params = new URLSearchParams(hash.split('?')[1] || '');
    
    document.querySelectorAll('.page').forEach(p => {
      p.classList.remove('active');
      p.style.display = 'none';
    });
    
    const earnPage = document.getElementById('page-earn');
    if (earnPage) {
      earnPage.style.display = 'block';
      earnPage.classList.add('active');
      
      // Force reinit to get new params
      earnPage.dataset.initialized = 'false';
      
      console.log('[App] Loading Earn page with params:', {
        session_id: params.get('session_id'),
        merchant_id: params.get('merchant_id'),
        charger_id: params.get('charger_id')
      });
      
      import('./pages/earn.js').then(module => {
        console.log('[App] Earn module loaded, initializing...');
        module.initEarn({
          session_id: params.get('session_id'),
          merchant_id: params.get('merchant_id'),
          charger_id: params.get('charger_id')
        }).catch(err => {
          console.error('[App] Error initializing Earn page:', err);
        });
      }).catch(err => {
        console.error('[App] Error loading Earn module:', err);
      });
    }
    return;
  }
  
  // Handle merchant dashboard
  if (hash.startsWith('#/merchant-dashboard')) {
    const params = new URLSearchParams(hash.split('?')[1] || '');
    const merchantId = params.get('merchant_id');
    
    if (merchantId) {
      document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
        p.style.display = 'none';
      });
      
      const dashboardPage = document.getElementById('page-merchant-dashboard');
      if (dashboardPage) {
        dashboardPage.style.display = 'block';
        dashboardPage.classList.add('active');
        
        import('./pages/merchantDashboard.js').then(module => {
          module.initMerchantDashboard({ merchant_id: merchantId });
        });
      }
      return;
    }
  }
  
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

// Track active tab for cleanup
let _activeTab = 'explore';

export async function setTab(tab){
  // Clean up Earn session if leaving Earn tab
  if (_activeTab === 'earn' && tab !== 'earn') {
    // Import cleanup function dynamically to avoid circular dependencies
    import('./pages/earn.js').then(module => {
      if (module.cleanupEarnSession) {
        module.cleanupEarnSession();
      }
    }).catch(() => {
      // Ignore import errors
    });
  }
  
  _activeTab = tab;
  
  // Map discover tab to explore page
  const pageMap = {
    'wallet': 'page-wallet',
    'discover': 'page-explore',
    'profile': 'page-profile'
  };
  
  const targetPageId = pageMap[tab] || `page-${tab}`;
  document.querySelectorAll('.page').forEach(p=>p.classList.toggle('active', p.id===targetPageId));
  document.querySelectorAll('.tabbar .tab').forEach(t=>t.classList.toggle('active', t.dataset.tab===tab));
  
  console.log(`[Nav][Tabs] Switched to ${tab}`);
  
  if(tab==='explore' || tab==='discover') {
    ensureMap();
    if(tab==='discover') {
      // Initialize explore page when switching to discover tab
      const exploreEl = document.getElementById('page-explore');
      if (exploreEl && !exploreEl.dataset.initialized) {
        const { initExplore } = await import('./pages/explore.js');
        initExplore();
        exploreEl.dataset.initialized = 'true';
      }
    }
  }
  if(tab==='activity') await initActivity();
  if(tab==='earn') await initEarn();
  if(tab==='wallet') {
    await initWallet();
  }
  if(tab==='profile') {
    await initMe();
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

// Register service worker for PWA
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js')
      .then((registration) => {
        console.log('Service Worker registered:', registration.scope);
      })
      .catch((error) => {
        console.log('Service Worker registration failed:', error);
      });
  });
}

// Global demo mode flag
const DEMO_MODE =
  new URLSearchParams(window.location.search).get('demo') === '1' ||
  localStorage.getItem('nerava_demo') === '1';

// Expose to window for console access
window.__neravaSetDemo = (on) => {
  if (on) {
    localStorage.setItem('nerava_demo', '1');
    window.NERAVA_DEMO_MODE = true;
  } else {
    localStorage.removeItem('nerava_demo');
    window.NERAVA_DEMO_MODE = false;
  }
  console.log('[DEMO] Demo mode now', on ? 'ON' : 'OFF', '– reload to apply');
};

// Set global flag
window.NERAVA_DEMO_MODE = DEMO_MODE;
if (DEMO_MODE) {
  console.log('[DEMO] Demo mode enabled via URL param or localStorage');
}

// Initialize app
// Initialize user on app load
async function initAuth() {
  try {
    const { apiMe, getCurrentUser } = await import('./core/api.js');
    const user = await apiMe();
    if (user) {
      console.log('[BOOT] Authenticated user:', user.email || user.id);
      window.NERAVA_USER = user;
      
      // Run demo flow if demo mode is enabled
      if (DEMO_MODE) {
        console.log('[DEMO] User authenticated, starting demo flow...');
        // Delay to let UI stabilize
        setTimeout(async () => {
          try {
            const { runDemoFlow } = await import('./core/demo-runner.js');
            await runDemoFlow();
          } catch (e) {
            console.error('[DEMO] Failed to start demo flow:', e);
          }
        }, 2000);
      }
    } else {
      console.log('[BOOT] No authenticated user - will prompt for login');
    }
  } catch (e) {
    console.warn('[BOOT] Failed to check auth status:', e.message);
  }
}

async function initApp() {
  // Check authentication status
  await initAuth();
  
  console.log('[BOOT] Using canonical /v1 backend (no pilot endpoints)');
  
  // Load demo state (banner removed - trigger demo from Swagger)
  await loadDemoState();
  
  // Add keyboard shortcut for dev tab
  document.addEventListener('keydown', (e)=>{ 
    if(e.key==='d' || e.key==='D'){ 
      location.hash='#/dev'; 
    } 
  });
  
  // Handle hash routing
  window.addEventListener('hashchange', handleHashRoute);
  handleHashRoute();  // Handle initial hash if present
  
  // Only set default tab if no hash route
  if (!location.hash || location.hash === '#') {
    setTab('wallet');
  }
  
  // Add bottom padding to all pages
  const pages = document.querySelectorAll('.page, #pageExplore, #pageCharge, #pageWallet, #pageMe, #pageClaim');
  pages.forEach(p => { 
    p.style.paddingBottom = `calc(84px + env(safe-area-inset-bottom, 12px))`; 
  });
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', async ()=>{ 
  // Check for payment success in URL
  const urlParams = new URLSearchParams(window.location.search);
  const paidParam = urlParams.get('paid');
  if (paidParam) {
    // Show payment success message
    showToast('🎉 Payment completed! Check your wallet for rewards.');
    // Clean up URL
    const newUrl = window.location.pathname + window.location.hash;
    window.history.replaceState({}, document.title, newUrl);
  }

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

  // Default to wallet tab on load (will be overridden by hash routes if present)
  if (!location.hash || location.hash === '#') {
    setTab('wallet');
  }
  // Gate on SSO; after SSO completes, it calls the loaders again.
  if (typeof ensureAuth === 'function' && !ensureAuth()) return;
  await loadBanner();
  await loadRecommendation();
  await loadWallet();
  await loadPrefs();
});

// Fullscreen functionality - only called from user gestures to avoid errors
function tryEnterFullscreen() {
  // Check if already in fullscreen or standalone mode
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches || 
                       (window.navigator.standalone === true) ||
                       document.referrer.includes('android-app://');
  
  if (isStandalone) {
    return; // Already in standalone mode, no need for fullscreen
  }
  
  // Check if already in fullscreen
  if (document.fullscreenElement || 
      document.webkitFullscreenElement || 
      document.mozFullScreenElement || 
      document.msFullscreenElement) {
    return; // Already fullscreen
  }
  
  // Try Fullscreen API (works on desktop and some mobile browsers)
  const elem = document.documentElement;
  
  try {
    if (elem.requestFullscreen) {
      elem.requestFullscreen().catch(() => {
        // Silently fail - fullscreen requires user gesture and may not always be available
      });
    } else if (elem.webkitRequestFullscreen) {
      elem.webkitRequestFullscreen();
    } else if (elem.webkitEnterFullscreen) {
      elem.webkitEnterFullscreen();
    } else if (elem.mozRequestFullScreen) {
      elem.mozRequestFullScreen();
    } else if (elem.msRequestFullscreen) {
      elem.msRequestFullscreen();
    }
  } catch (err) {
    // Silently fail - fullscreen may not be supported or require user gesture
  }
}

// Export for use elsewhere - only call from explicit user interactions
if (typeof window !== 'undefined') {
  window.tryEnterFullscreen = tryEnterFullscreen;
  
  // Only attempt fullscreen on first explicit user interaction (button clicks, etc.)
  // Don't spam on every touch/click, just provide the function for buttons to call
  let fullscreenAttempted = false;
  
  // Add a subtle fullscreen button or trigger on first meaningful interaction
  document.addEventListener('click', (e) => {
    // Only try once, and only on button clicks or navigation actions
    if (!fullscreenAttempted && (
      e.target.tagName === 'BUTTON' || 
      e.target.closest('button') ||
      e.target.closest('[role="button"]')
    )) {
      fullscreenAttempted = true;
      tryEnterFullscreen();
    }
  }, { once: true, passive: true });
}

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

// Backend healthcheck (skipped - using v1 endpoints directly)
async function checkBackend() {
  // No longer calling deprecated /v1/pilot/app/bootstrap
  // App now uses canonical /v1/* endpoints directly (auth/me, drivers/merchants/nearby, etc.)
  console.log('[BOOTSTRAP SKIPPED] Using canonical /v1 endpoints - no pilot bootstrap needed');
  return true;
}

window.addEventListener('load', async ()=>{
  // Check backend connectivity
  await checkBackend();
  
  // Log tab layout initialization
  console.log('[Nav][Tabs] Layout: flex spacing enabled');
  
  // Start with wallet tab by default
  setTab('wallet');
  // lazy import to avoid cyclic loads
  const { initExplore } = await import('./pages/explore.js');
  initExplore();
  await loadBanner();
  await loadWallet();
  await loadPrefs();
  
  // Request fullscreen (user gesture required, so this will be triggered by button clicks)
  // Fullscreen is handled by tryEnterFullscreen() on user interaction
});

// Initialize activity page when tab is switched
async function initActivity() {
  const activityEl = document.getElementById('page-activity');
  if (activityEl && !activityEl.dataset.initialized) {
    const { initActivityPage } = await import(`./pages/activity.js?v=${Date.now()}`);
    await initActivityPage(activityEl);
    activityEl.dataset.initialized = 'true';
  }
}

// Initialize earn page when tab is switched
async function initEarn() {
  const earnEl = document.getElementById('page-earn');
  if (earnEl) {
    // Clear initialization flag when starting new session (hash params indicate new session)
    const hash = window.location.hash;
    if (hash.includes('merchant_id=') && hash.includes('charger_id=')) {
      earnEl.dataset.initialized = 'false';  // Force reinit with new params
    }
    
    // Get params from URL if available
    const urlParams = new URLSearchParams(hash.split('?')[1] || '');
    const params = {
      session_id: urlParams.get('session_id'),
      merchant_id: urlParams.get('merchant_id'),
      charger_id: urlParams.get('charger_id')
    };
    
    if (!earnEl.dataset.initialized || earnEl.dataset.initialized === 'false') {
      const { initEarn } = await import(`./pages/earn.js?v=${Date.now()}`);
      await initEarn(params);  // Pass params to initEarn
      earnEl.dataset.initialized = 'true';
    }
  }
}

// Initialize wallet page when tab is switched
async function initWallet() {
  const walletEl = document.getElementById('page-wallet');
  console.log('initWallet called, walletEl:', walletEl);
  if (walletEl && !walletEl.dataset.initialized) {
    console.log('Initializing wallet page...');
    const { initWalletPage } = await import('./pages/wallet-new.js');
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
    const { initMePage } = await import(`./pages/me.js?v=${Date.now()}`);
    await initMePage(meEl);
    meEl.dataset.initialized = 'true';
    console.log('Me page initialized');
  }
}

// Export functions for use by other modules
// Removed exports to avoid "does not provide an export named" errors