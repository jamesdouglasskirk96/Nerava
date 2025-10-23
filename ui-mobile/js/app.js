(() => {
  const HUB = { name:'Nerava Hub', lat:30.4022, lng:-97.7249, city:'Domain, Austin' };

  const $  = (id)=>document.getElementById(id);
  const on = (el, ev, fn)=>el && el.addEventListener(ev, fn, {passive:true});

  function setActive(tabName){
    // tabs
    ['Explore','Charge','Wallet','Profile'].forEach(n=>{
      const btn = $('tab'+n);
      if(btn) btn.classList.toggle('active', n===tabName);
    });
    // pages
    ['Explore','Charge','Wallet','Profile'].forEach(n=>{
      const pg = $('page'+n);
      if(pg) pg.classList.toggle('active', n===tabName);
    });
    // banner only on Explore
    const banner = $('dealBanner');
    if(banner) banner.style.display = (tabName==='Explore') ? '' : 'none';
  }

  // Map & route
  let map, routingCtl;
  function ensureMap(){
    if(typeof L==='undefined'){ setTimeout(ensureMap,120); return; }
    if(map) return;
    map = L.map('map',{ zoomControl:false });
    map.setView([HUB.lat, HUB.lng], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      {maxZoom:19, attribution:'&copy; OpenStreetMap'}).addTo(map);

    // Hub marker
    L.circleMarker([HUB.lat, HUB.lng], {radius:8, color:'#55ffc7', weight:4, fill:true, fillOpacity:.5})
      .addTo(map).bindPopup(HUB.name);
  }

  function drawRouteToHub(){
    if(typeof L==='undefined' || !map || !L.Routing){ return; }

    // Remove prior route
    if(routingCtl){ map.removeControl(routingCtl); routingCtl = null; }

    const fallbackStart = [30.3982,-97.7239]; // a nearby point if geolocation denied

    const makeControl = (start) => {
      routingCtl = L.Routing.control({
        waypoints: [ L.latLng(start[0],start[1]), L.latLng(HUB.lat,HUB.lng) ],
        routeWhileDragging:false,
        addWaypoints:false,
        draggableWaypoints:false,
        fitSelectedRoutes:true,
        show:false
      }).addTo(map);
    };

    if(navigator.geolocation){
      navigator.geolocation.getCurrentPosition(
        pos => makeControl([pos.coords.latitude, pos.coords.longitude]),
        _err => makeControl(fallbackStart),
        {enableHighAccuracy:true, maximumAge:60000, timeout:4000}
      );
    } else {
      makeControl(fallbackStart);
    }
  }

  function wireUI(){
    // Tabs
    on($('tabExplore'),'click', ()=>setActive('Explore'));
    on($('tabCharge'), 'click', ()=>setActive('Charge'));
    on($('tabWallet'), 'click', ()=>setActive('Wallet'));
    on($('tabProfile'),'click', ()=>setActive('Profile'));

    // Charge here -> go to Charge page
    on($('chargeHereBtn'),'click', ()=>{
      setActive('Charge');
    });
  }

  // ==== Snackbar / Toast ====
  function showToast(msg, ok = true) {
    const el = document.createElement('div');
    el.textContent = msg;
    el.style.cssText = `
      position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%);
      background: ${ok ? '#0B2A4A' : '#b91c1c'}; color:#fff; padding:10px 14px; border-radius:999px;
      box-shadow:0 8px 24px rgba(0,0,0,0.25); z-index: 2000; font-weight:600;`;
    document.body.appendChild(el);
    setTimeout(() => { el.remove(); }, 2400);
  }

  // ==== Session state ====
  const SESSION_KEY = 'nerava_active_session';
  function getActiveSession() {
    try { return JSON.parse(localStorage.getItem(SESSION_KEY) || 'null'); } catch { return null; }
  }
  function setActiveSession(s) {
    if (s) localStorage.setItem(SESSION_KEY, JSON.stringify(s));
    else localStorage.removeItem(SESSION_KEY);
  }

  // ==== Reward preview ====
  async function fetchWindows() {
    try {
      const r = await fetch('/v1/energyhub/windows');
      return await r.json();
    } catch { return []; }
  }
  async function refreshRewardPreview() {
    const cont = document.getElementById('rewardPreview');
    const title = document.getElementById('rewardPreviewText');
    const sub = document.getElementById('rewardPreviewSub');
    if (!cont || !title || !sub) return;

    const windows = await fetchWindows();
    const active = windows.find(w => w.active_now);
    if (!active) { cont.style.display = 'none'; return; }

    const isGreen = active.id === 'green_hour';
    title.textContent = isGreen
      ? 'Cheaper charging now — 2× rewards'
      : 'Cheaper charging now';
    sub.textContent = `Window: ${active.label} (${active.start_utc}–${active.end_utc} UTC) • Grid $/kWh ${active.price_per_kwh} × ${active.multiplier}x`;
    cont.style.display = 'block';
  }

  // ==== Explore banner (polish only; you already have a version) ====
  async function refreshIncentiveBanner() {
    const banner = document.getElementById('incentive-banner');
    const exploreTab = document.getElementById('tabExplore');
    if (!banner || !exploreTab) return;

    const exploreVisible = exploreTab.classList.contains('active') || exploreTab.style.display !== 'none';
    if (!exploreVisible) { banner.style.display = 'none'; return; }

    const windows = await fetchWindows();
    const active = windows.find(w => w.active_now);
    if (!active) { banner.style.display = 'none'; return; }

    banner.textContent = active.id === 'green_hour'
      ? 'Cheaper charging now — 2× rewards'
      : 'Cheaper charging now';
    banner.style.display = 'block';
  }

  // ==== Charge controls ====
  let sessionTimer = null;
  function formatElapsed(ms) {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60), r = s % 60;
    const h = Math.floor(m / 60), rm = m % 60;
    return h ? `${h}h ${rm}m` : `${rm}m ${r}s`;
  }
  function syncChargeUI() {
    const startBtn = document.getElementById('btnStartCharge');
    const stopBtn = document.getElementById('btnStopCharge');
    const activeBox = document.getElementById('activeSession');
    const sidShort = document.getElementById('sessionIdShort');
    const startAt = document.getElementById('sessionStart');
    const elapsed = document.getElementById('sessionElapsed');

    const s = getActiveSession();
    if (!startBtn || !stopBtn || !activeBox) return;

    if (!s) {
      startBtn.disabled = false;
      stopBtn.disabled = true;
      activeBox.style.display = 'none';
      if (sessionTimer) { clearInterval(sessionTimer); sessionTimer = null; }
    } else {
      startBtn.disabled = true;
      stopBtn.disabled = false;
      activeBox.style.display = 'block';
      sidShort.textContent = s.session_id.slice(0, 8) + '…';
      startAt.textContent = new Date(s.started_at).toLocaleTimeString();
      if (sessionTimer) clearInterval(sessionTimer);
      sessionTimer = setInterval(() => {
        const ms = Date.now() - new Date(s.started_at).getTime();
        elapsed.textContent = formatElapsed(ms);
      }, 1000);
    }
  }

  async function startCharge() {
    try {
      const payload = { user_id: 'demo@nerava.app', hub_id: 'hub_domain_A' };
      const r = await fetch('/v1/energyhub/events/charge-start', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!r.ok) throw new Error('charge_start_failed');
      const jd = await r.json();
      const s = {
        session_id: jd.session_id,
        started_at: new Date().toISOString()
      };
      setActiveSession(s);
      syncChargeUI();
      showToast('Charging started');
    } catch (e) {
      showToast('Could not start session', false);
      console.error(e);
    }
  }

  function promptForKWh() {
    const dlg = document.getElementById('kwhDialog');
    if (dlg && typeof dlg.showModal === 'function') {
      dlg.showModal();
    } else {
      const val = prompt('How many kWh did you add? (e.g. 18.6)');
      return val ? parseFloat(val) : null;
    }
    return null; // dialog path will resolve via click handler
  }

  async function stopChargeWith(kwh) {
    const s = getActiveSession();
    if (!s) return;
    try {
      const r = await fetch('/v1/energyhub/events/charge-stop', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: s.session_id, kwh_consumed: kwh })
      });
      if (!r.ok) throw new Error('charge_stop_failed');
      const jd = await r.json();

      // Clear session
      setActiveSession(null);
      syncChargeUI();

      // Show reward
      const earned = jd.total_reward_usd?.toFixed?.(2);
      showToast(jd.message || `Wallet credited $${earned}`);

      // Add to client-side Recent Activity
      const li = document.createElement('li');
      li.textContent = `${new Date().toLocaleString()} — ${kwh} kWh • +$${earned}`;
      document.getElementById('recentActivity')?.prepend(li);

      // If you already surface wallet balance elsewhere, trigger a refresh there
      // (e.g., fetch('/v1/wallet?user_id=demo@nerava.app') and update UI)
    } catch (e) {
      showToast('Could not stop/credit session', false);
      console.error(e);
    }
  }

  function wireChargeHandlers() {
    const startBtn = document.getElementById('btnStartCharge');
    const stopBtn = document.getElementById('btnStopCharge');
    const dlg = document.getElementById('kwhDialog');
    const kwhInput = document.getElementById('kwhInput');

    if (startBtn) startBtn.addEventListener('click', async () => {
      await startCharge();
    });

    if (stopBtn) stopBtn.addEventListener('click', () => {
      const immediate = promptForKWh();
      if (immediate !== null) {
        const v = parseFloat(immediate);
        if (!isNaN(v) && v > 0) stopChargeWith(v);
        else showToast('Please enter a valid kWh amount', false);
      }
    });

    if (dlg) {
      dlg.addEventListener('close', () => {
        if (dlg.returnValue === 'confirm') {
          const v = parseFloat(kwhInput.value);
          if (!isNaN(v) && v > 0) stopChargeWith(v);
          else showToast('Please enter a valid kWh amount', false);
        }
      });
    }
  }

  // boot
  document.addEventListener('DOMContentLoaded', ()=>{
    wireUI();
    ensureMap();
    // draw a route after map is ready
    setTimeout(()=>{ ensureMap(); drawRouteToHub(); }, 500);
    
    // Initialize charging flow
    refreshRewardPreview();
    refreshIncentiveBanner();
    setInterval(refreshRewardPreview, 30000);
    setInterval(refreshIncentiveBanner, 30000);

    wireChargeHandlers();
    syncChargeUI();

    // If you have bottom nav, hook into it so we refresh when switching tabs:
    const nav = document.getElementById('bottom-nav');
    if (nav) nav.addEventListener('click', () => setTimeout(() => {
      refreshRewardPreview();
      refreshIncentiveBanner();
    }, 80));
  });
})();
