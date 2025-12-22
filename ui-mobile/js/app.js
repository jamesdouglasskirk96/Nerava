// Main app controller
// API base URL is now determined dynamically in api.js based on environment
// No need to set localStorage.NERAVA_URL unless explicitly overriding

import { loadDemoState } from './core/demo.js';
import { apiGet, apiPost } from './core/api.js';
import { ensureMap, drawRoute, clearRoute, getMap } from './core/map.js';

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

// === Auth flow (production auth v1) ===
// Demo mode auto-login is now gated behind DEMO_MODE env flag

async function checkAuth() {
  // Check if user is authenticated
  const { isAuthenticated } = await import('./core/auth.js');
  return isAuthenticated();
}

async function ensureAuth() {
  // Auth guard: redirect to login if not authenticated
  // Skip for login page itself
  if (window.location.hash === '#/login' || window.location.hash.startsWith('#/login')) {
    return true;
  }
  
  const authenticated = await checkAuth();
  
  if (!authenticated) {
    // Check if DEMO_MODE is enabled (via URL param or localStorage flag)
    const urlParams = new URLSearchParams(window.location.search);
    const demoMode = urlParams.get('demo') === '1' || localStorage.getItem('nerava_demo') === '1';
    
    if (demoMode) {
      // Demo mode: allow access but log warning
      console.warn('[Auth] DEMO_MODE enabled - skipping auth check');
      return true;
    }
    
    // Redirect to login
    console.log('[Auth] Not authenticated - redirecting to login');
    window.location.hash = '#/login';
    return false;
  }
  
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
async function handleHashRoute() {
  const hash = location.hash;
  console.log('[App] handleHashRoute called with hash:', hash);
  
  // Send telemetry event for tab switch
  if (hash && typeof window !== 'undefined') {
    try {
      const { apiSendTelemetryEvent } = await import('./core/api.js');
      apiSendTelemetryEvent({
        event: 'TAB_SWITCHED',
        ts: Date.now(),
        page: hash,
        meta: {}
      }).catch(() => {});
    } catch (e) {
      // Swallow errors - telemetry is optional
    }
  }
  
  // Handle login page
  if (hash === '#/login' || hash.startsWith('#/login')) {
    console.log('[App] Login route detected, showing login page...');
    document.querySelectorAll('.page').forEach(p => {
      p.classList.remove('active');
      p.style.display = 'none';
    });
    
    let loginPage = document.getElementById('page-login');
    if (!loginPage) {
      console.log('[App] Creating login page element...');
      loginPage = document.createElement('section');
      loginPage.id = 'page-login';
      loginPage.className = 'page';
      const appEl = document.getElementById('app');
      if (appEl) {
        appEl.appendChild(loginPage);
      } else {
        console.error('[App] Cannot find #app element to append login page');
        return;
      }
    }
    
    // Ensure login page is visible - CSS will handle the rest with !important
    loginPage.classList.add('active');
    loginPage.style.display = 'block';
    loginPage.style.visibility = 'visible';
    loginPage.style.opacity = '1';
    loginPage.style.zIndex = '10000';
    loginPage.style.position = 'fixed';
    loginPage.style.top = '0';
    loginPage.style.left = '0';
    loginPage.style.right = '0';
    loginPage.style.bottom = '0';
    loginPage.style.width = '100vw';
    loginPage.style.height = '100vh';
    console.log('[App] Login page element shown, initializing...');
    
    // Initialize login page if not already initialized
    if (!loginPage.dataset.initialized) {
      try {
        const { initLoginPage } = await import('./pages/login.js');
        console.log('[App] Login page module loaded, calling initLoginPage...');
        await initLoginPage(loginPage);
        loginPage.dataset.initialized = 'true';
        console.log('[App] Login page initialized successfully');
      } catch (error) {
        console.error('[App] Failed to initialize login page:', error);
      }
    } else {
      console.log('[App] Login page already initialized');
    }
    
    return;
  }
  
  // Auth guard for other routes
  const authOk = await ensureAuth();
  if (!authOk) {
    return; // Redirected to login
  }
  
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
  
  // Handle virtual card page
  if (hash.startsWith('#/virtual-card')) {
    document.querySelectorAll('.page').forEach(p => {
      p.classList.remove('active');
      p.style.display = 'none';
    });
    
    let virtualCardPage = document.getElementById('page-virtual-card');
    if (!virtualCardPage) {
      virtualCardPage = document.createElement('section');
      virtualCardPage.id = 'page-virtual-card';
      virtualCardPage.className = 'page page-padded';
      document.getElementById('app').appendChild(virtualCardPage);
    }
    
    virtualCardPage.style.display = 'block';
    virtualCardPage.classList.add('active');
    
    import('./pages/virtual-card.js').then(module => {
      module.initVirtualCardPage(virtualCardPage);
    }).catch(err => {
      console.error('[App] Error loading virtual card page:', err);
    });
    return;
  }
  
  // Handle wallet pass page
  if (hash.startsWith('#/wallet-pass')) {
    document.querySelectorAll('.page').forEach(p => {
      p.classList.remove('active');
      p.style.display = 'none';
    });
    
    let walletPassPage = document.getElementById('page-wallet-pass');
    if (!walletPassPage) {
      walletPassPage = document.createElement('section');
      walletPassPage.id = 'page-wallet-pass';
      walletPassPage.className = 'page page-padded';
      document.getElementById('app').appendChild(walletPassPage);
    }
    
    walletPassPage.style.display = 'block';
    walletPassPage.classList.add('active');
    
    import('./pages/wallet-pass.js').then(module => {
      module.initWalletPassPage(walletPassPage);
    }).catch(err => {
      console.error('[App] Error loading wallet pass page:', err);
    });
    return;
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
  // Don't switch tabs if we're on the login page
  if (window.location.hash === '#/login' || window.location.hash.startsWith('#/login')) {
    console.log('[App] setTab() called but login route is active, ignoring');
    return;
  }
  
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
  
  // Clean up wallet timers if leaving wallet tab
  if (_activeTab === 'wallet' && tab !== 'wallet') {
    const walletEl = document.getElementById('page-wallet');
    if (walletEl?._walletCleanup) {
      walletEl._walletCleanup();
    }
    // Also call module-level cleanup if exported
    import('./pages/wallet-new.js').then(module => {
      if (module.stopWalletTimers) {
        module.stopWalletTimers();
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
  const targetPage = document.getElementById(targetPageId);
  
  // Remove active from all pages FIRST (prevents flash of old content)
  document.querySelectorAll('.page').forEach(p => {
    p.classList.remove('active');
  });
  
  // Update tab indicators
  document.querySelectorAll('.tabbar .tab').forEach(t=>t.classList.toggle('active', t.dataset.tab===tab));
  
  console.log(`[Nav][Tabs] Switched to ${tab}`);
  
  // Initialize page content BEFORE marking as active (prevents flash)
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
    // Mark page active after initialization
    if (targetPage) targetPage.classList.add('active');
  } else if(tab==='activity') {
    await initActivity();
    if (targetPage) targetPage.classList.add('active');
  } else if(tab==='earn') {
    await initEarn();
    if (targetPage) targetPage.classList.add('active');
  } else if(tab==='wallet') {
    await initWallet();
    
    // If wallet should refresh (e.g., after redemption), trigger immediate refresh
    const walletEl = document.getElementById('page-wallet');
    if (sessionStorage.getItem('nerava_wallet_should_refresh') === 'true') {
      sessionStorage.removeItem('nerava_wallet_should_refresh');
      if (walletEl && walletEl.dataset.initialized === 'true') {
        // Dispatch refresh event immediately to trigger wallet refresh
        window.dispatchEvent(new CustomEvent('nerava:wallet:invalidate'));
      }
    }
    if (targetPage) targetPage.classList.add('active');
  } else if(tab==='profile') {
    await initMe();
    if (targetPage) targetPage.classList.add('active');
  } else {
    // Fallback: mark page active if no specific initialization
    if (targetPage) targetPage.classList.add('active');
  }
  
  // Hide loading screen if still visible (e.g., on first tab switch)
  hideLoadingScreen();
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

// Hide loading screen after app is ready
function hideLoadingScreen() {
  const loadingScreen = document.getElementById('app-loading-screen');
  if (loadingScreen) {
    loadingScreen.style.display = 'none';
    loadingScreen.classList.add('hidden', 'removed');
  }
}

// Show loading screen (call this at start of slow operations if needed)
function showLoadingScreen() {
  const loadingScreen = document.getElementById('app-loading-screen');
  if (loadingScreen) {
    loadingScreen.classList.remove('hidden', 'removed');
    loadingScreen.style.display = 'flex';
  }
}

async function initApp() {
  console.log('[App] initApp() called');
  
  // Handle hash routing FIRST - this is critical for login page
  console.log('[App] Registering hashchange handler and calling handleHashRoute');
  window.addEventListener('hashchange', handleHashRoute);
  handleHashRoute();  // Handle initial hash if present
  
  try {
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
    
    // Only set default tab if no hash route
    if (!location.hash || location.hash === '#') {
      setTab('wallet');
    }
    
    // Add bottom padding to all pages
    const pages = document.querySelectorAll('.page, #pageExplore, #pageCharge, #pageWallet, #pageMe, #pageClaim');
    pages.forEach(p => { 
      p.style.paddingBottom = `calc(84px + env(safe-area-inset-bottom, 12px))`; 
    });
    
    // Hide loading screen after initialization is complete
    hideLoadingScreen();
  } catch (error) {
    console.error('[App] initApp() failed:', error);
    // Even if init fails, hash routing should still work
    // Still hide loading screen on error
    hideLoadingScreen();
  }
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
  // Auth guard - check authentication
  const authOk = await ensureAuth();
  if (!authOk) {
    return; // Redirected to login
  }
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
  // Initialize app (this sets up hash routing)
  await initApp();
  
  // Check backend connectivity
  await checkBackend();
  
  // Log tab layout initialization
  console.log('[Nav][Tabs] Layout: flex spacing enabled');
  
  // Don't set default tab if we're on login route
  if (window.location.hash !== '#/login' && !window.location.hash.startsWith('#/login')) {
    // Start with wallet tab by default
    setTab('wallet');
  }
  
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
  if (walletEl) {
    // Cleanup previous intervals if wallet was already initialized
    if (walletEl._walletCleanup) {
      walletEl._walletCleanup();
    }
    // Also call module-level cleanup
    try {
      const { stopWalletTimers } = await import('./pages/wallet-new.js');
      if (stopWalletTimers) {
        stopWalletTimers();
      }
    } catch {
      // Ignore import errors
    }
    
    if (!walletEl.dataset.initialized) {
      console.log('Initializing wallet page...');
      const { initWalletPage } = await import('./pages/wallet-new.js');
      await initWalletPage(walletEl);
      walletEl.dataset.initialized = 'true';
      console.log('Wallet page initialized');
    }
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