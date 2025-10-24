// Main app controller
window.Nerava = window.Nerava || {};

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
function initApp() {
  wireTabs();
  
  // Set initial tab
  setActive('Explore');
  
  // Add bottom padding to all pages
  const pages = document.querySelectorAll('.page, #pageExplore, #pageCharge, #pageWallet, #pageMe, #pageClaim');
  pages.forEach(p => { 
    p.style.paddingBottom = `calc(84px + env(safe-area-inset-bottom, 12px))`; 
  });
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);