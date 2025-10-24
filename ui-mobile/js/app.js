// Main app controller
window.Nerava = window.Nerava || {};

// Tab management
const Tabs = (() => {
  let active = 'Explore';
  const listeners = [];

  function setActive(tab) {
    if (active === tab) return;
    
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
      page.style.display = 'none';
    });
    
    // Show active page
    const activePage = document.getElementById(`page${tab}`);
    if (activePage) {
      activePage.style.display = 'block';
    }
    
    // Update nav
    document.querySelectorAll('.tab').forEach(btn => {
      btn.classList.remove('active');
    });
    const activeBtn = document.getElementById(`tab${tab}`);
    if (activeBtn) {
      activeBtn.classList.add('active');
    }
    
    active = tab;
    
    // Call page init
    if (window.Nerava.pages && window.Nerava.pages[tab.toLowerCase()]) {
      window.Nerava.pages[tab.toLowerCase()].init();
    }
    
    // Notify listeners
    listeners.forEach(fn => fn(active));
  }

  function getActive() {
    return active;
  }

  function onChange(callback) {
    listeners.push(callback);
  }

  return { setActive, getActive, onChange };
})();

// Wire tab buttons
function wireTabs() {
  document.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.id.replace('tab', '');
      Tabs.setActive(tab);
    });
  });
}

// Initialize app
function initApp() {
  wireTabs();
  
  // Set initial tab
  Tabs.setActive('Explore');
  
  // Add bottom padding to all pages
  const pages = document.querySelectorAll('.page, #pageExplore, #pageCharge, #pageWallet, #pageMe, #pageClaim');
  pages.forEach(p => { 
    p.style.paddingBottom = `calc(96px + env(safe-area-inset-bottom, 12px))`; 
  });
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);