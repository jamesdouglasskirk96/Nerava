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

  // ==== Streak functionality ====
  const STREAK_KEY = 'nerava_charging_streak';
  const LAST_CHARGE_KEY = 'nerava_last_charge_date';
  
  function getStreak() {
    try { return parseInt(localStorage.getItem(STREAK_KEY) || '0'); } catch { return 0; }
  }
  
  function incStreak(reset = false) {
    if (reset) {
      localStorage.setItem(STREAK_KEY, '0');
      localStorage.removeItem(LAST_CHARGE_KEY);
      return 0;
    }
    
    const today = new Date().toDateString();
    const lastCharge = localStorage.getItem(LAST_CHARGE_KEY);
    
    if (lastCharge === today) {
      return getStreak(); // Already charged today
    }
    
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toDateString();
    
    let newStreak = 1;
    if (lastCharge === yesterdayStr) {
      newStreak = getStreak() + 1;
    }
    
    localStorage.setItem(STREAK_KEY, newStreak.toString());
    localStorage.setItem(LAST_CHARGE_KEY, today);
    return newStreak;
  }
  
  function updateStreakDisplay() {
    const streak = getStreak();
    const streakEl = document.querySelector('.streak-text');
    if (streakEl) {
      streakEl.textContent = `${streak}-day charging streak 🔥`;
    }
  }

  // Wallet progress animation
  function setWalletProgress(amountNowUSD, tierTargetUSD = 25){
    const bar = document.querySelector('.wallet-progress .bar');
    if (!bar) return;
    const pct = Math.max(0, Math.min(100, (amountNowUSD / tierTargetUSD) * 100));
    // transition is defined in CSS; just set width
    requestAnimationFrame(()=>{ bar.style.width = pct + '%'; });
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

    // Pulse Start button when Green Hour is active
    const startBtn = document.getElementById('btnStartCharge');
    if (startBtn && window.Animations) {
      if (active.id === 'green_hour' && typeof window.Animations.greenPulse === 'function') {
        window.Animations.greenPulse(startBtn);
      } else if (typeof window.Animations.stopGreenPulse === 'function') {
        window.Animations.stopGreenPulse(startBtn);
      }
    }

    const newText = active.id === 'green_hour'
      ? '⚡ Green Hour Active — 2× Rewards'
      : 'Cheaper charging now';
    
    // Animate banner transition if text changed
    if (banner.textContent !== newText && banner.style.display === 'block') {
      if (window.Animations) {
        window.Animations.bannerTransition(banner);
      }
    }
    
    banner.textContent = newText;
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
    const stopBtn  = document.getElementById('btnStopCharge');
    const activeBox = document.getElementById('activeSession');
    const sidShort = document.getElementById('sessionIdShort');
    const startAt  = document.getElementById('sessionStart');
    const elapsed  = document.getElementById('sessionElapsed');

    const s = getActiveSession();
    if (!startBtn || !stopBtn || !activeBox) return;

    // Debug logging (dev only)
    console.log('[nerava] syncChargeUI:', {
      hasSession: !!s,
      sessionId: s?.session_id?.slice(0, 8),
      startedAt: s?.started_at,
      startBtnDisabled: startBtn.disabled,
      stopBtnDisabled: stopBtn.disabled
    });

    // Ensure buttons are interactable (z-index above map/route)
    [startBtn, stopBtn].forEach(b => { if (b) b.style.zIndex = '1000'; });

    if (!s) {
      startBtn.disabled = false;
      stopBtn.disabled  = true;
      activeBox.style.display = 'none';
      if (sessionTimer) { clearInterval(sessionTimer); sessionTimer = null; }
      return;
    }

    // When a session exists:
    startBtn.disabled = true;
    stopBtn.disabled  = false;
    activeBox.style.display = 'block';

    sidShort.textContent = (s.session_id || '').slice(0, 8) + '…';
    const startedAt = s.started_at ? new Date(s.started_at) : new Date();
    startAt.textContent = startedAt.toLocaleTimeString();

    if (sessionTimer) clearInterval(sessionTimer);
    sessionTimer = setInterval(() => {
      const ms = Date.now() - startedAt.getTime();
      elapsed.textContent = formatElapsed(ms);
    }, 1000);
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
      
      // Animate charge start
      const startBtn = document.getElementById('btnStartCharge');
      if (startBtn && window.Animations) {
        window.Animations.chargeStart(startBtn);
      }
      
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
      const earnedNum = Number(jd.total_reward_usd ?? 0);
      const earnedFixed = earnedNum.toFixed(2);
      showToast(jd.message || `Wallet credited $${earnedFixed}`);

      // Handle streak logic
      const windows = await fetchWindows();
      const activeWindow = windows.find(w => w.active_now);
      if (activeWindow) {
        const newStreak = incStreak();
        if (window.Animations && window.Animations.streakCelebrate) window.Animations.streakCelebrate();
        showToast(`Nice timing — streak +1! 🔥 (${newStreak} days)`);
      } else {
        incStreak(true); // Reset streak if not in active window
      }
      
      updateStreakDisplay();

      // Add to cumulative kWh total
      addCumulativeKwh(kwh);

      // Update wallet balance display with animation
      updateWalletBalance();
      
      // Animate wallet balance increment
      const walletBalance = document.getElementById('wallet-balance');
      if (walletBalance && window.Animations) {
        const currentBalance = parseFloat(String(walletBalance.textContent).replace('$', '')) || 0;
        const newBalance = currentBalance + earnedNum;
        if (window.Animations && window.Animations.chargeStop) {
          window.Animations.chargeStop(walletBalance, currentBalance, newBalance);
        }
        walletBalance.textContent = `$${newBalance.toFixed(2)}`;
        
        // Animate wallet progress bar
        setWalletProgress(newBalance % 25, 25); // naive example; adapt to your tier math
      }

      // If you already surface wallet balance elsewhere, trigger a refresh there
      // (e.g., fetch('/v1/wallet?user_id=demo@nerava.app') and update UI)
    } catch (e) {
      showToast('Could not stop/credit session', false);
      console.error(e);
    }
  }
  
  function updateWalletBalance() {
    // Animate balance increment
    const balanceEl = document.getElementById('wallet-balance');
    if (balanceEl) {
      // Add animation class for visual feedback
      balanceEl.classList.add('balance-updated');
      setTimeout(() => balanceEl.classList.remove('balance-updated'), 1000);
    }
  }

  function wireChargeHandlers() {
    const startBtn = document.getElementById('btnStartCharge');
    const stopBtn  = document.getElementById('btnStopCharge');   // ensure this ID exists in HTML
    const dlg      = document.getElementById('kwhDialog');
    const kwhInput = document.getElementById('kwhInput');

    // Defensive: surface if IDs are missing
    if (!startBtn) console.warn('[nerava] Missing #btnStartCharge');
    if (!stopBtn)  console.warn('[nerava] Missing #btnStopCharge');
    if (!dlg)      console.warn('[nerava] Missing #kwhDialog');
    if (!kwhInput) console.warn('[nerava] Missing #kwhInput');

    // Make dialog clickable above everything
    if (dlg) dlg.style.zIndex = '3000';

    if (startBtn) startBtn.addEventListener('click', async () => {
      // Avoid double-click races
      if (startBtn.disabled) return;
      startBtn.disabled = true;
      try {
        await startCharge();
      } finally {
        // startCharge() will re-sync UI; re-enable if session didn't start
        const s = getActiveSession();
        if (!s) startBtn.disabled = false;
      }
    });

    // IMPORTANT: Stop must open the kWh prompt or dialog
    if (stopBtn) stopBtn.addEventListener('click', () => {
      if (stopBtn.disabled) return;
      const immediate = promptForKWh();
      if (immediate !== null) {
        const v = parseFloat(immediate);
        if (!isNaN(v) && v > 0) stopChargeWith(v);
        else showToast('Please enter a valid kWh amount', false);
      }
    }, { passive: true });

    // Dialog confirm path
    if (dlg) {
      dlg.addEventListener('close', () => {
        if (dlg.returnValue === 'confirm') {
          const v = parseFloat(kwhInput.value);
          if (!isNaN(v) && v > 0) stopChargeWith(v);
          else showToast('Please enter a valid kWh amount', false);
        }
      });
      // Ensure dialog buttons have proper returnValue binding
      dlg.querySelectorAll('[data-return]').forEach(btn => {
        btn.addEventListener('click', () => { dlg.returnValue = btn.getAttribute('data-return'); dlg.close(); });
      });
    }
  }

  // ==== Cumulative kWh Tracking ====
  const CUMULATIVE_KWH_KEY = 'nerava_cumulative_kwh';
  function getCumulativeKwh(){ 
    try { 
      return parseFloat(localStorage.getItem(CUMULATIVE_KWH_KEY) || '0'); 
    } catch { 
      return 0; 
    } 
  }
  function addCumulativeKwh(kwh){ 
    const current = getCumulativeKwh();
    const newTotal = current + kwh;
    localStorage.setItem(CUMULATIVE_KWH_KEY, newTotal.toString());
    updateCumulativeDisplay();
    return newTotal;
  }
  function updateCumulativeDisplay(){
    const totalEl = document.getElementById('totalKwh');
    if (totalEl) {
      totalEl.textContent = getCumulativeKwh().toFixed(1);
    }
  }

  // --- Appleish controllers ---
  async function fetchHubSummary(lat, lng) {
    const r = await fetch(`/v1/hubs/summary?lat=${lat}&lng=${lng}`);
    return r.ok ? r.json() : { name:'Nerava Hub', chargers:12, pricing:'Paid', distance_mi:3.4, phone:null, website:null };
  }
  async function fetchNearbyPlaces(lat, lng) {
    const r = await fetch(`/v1/places/nearby?lat=${lat}&lng=${lng}`);
    return r.ok ? r.json() : { places:[] };
  }
  async function fetchPlaceActivity(hub_id) {
    const r = await fetch(`/v1/social/feed?hub_id=${encodeURIComponent(hub_id)}`);
    return r.ok ? r.json() : { items:[] };
  }

  function renderHubSummary(summary){
    const titleEl = document.getElementById('place-title');
    const chargersEl = document.getElementById('chip_chargers');
    const pricingEl = document.getElementById('chip_pricing');
    const distanceEl = document.getElementById('chip_distance');
    const chargerListEl = document.getElementById('charger-list');

    if (titleEl) titleEl.textContent = summary.name;
    if (chargersEl) chargersEl.textContent = `${summary.chargers} Chargers`;
    if (pricingEl) pricingEl.textContent = summary.pricing || '—';
    if (distanceEl) distanceEl.textContent = `${summary.distance_mi ?? '—'} mi`;

    if (chargerListEl) {
      chargerListEl.innerHTML = '';
      (summary.models || [{vendor:'Tesla', speed_kw:250, count:summary.chargers}]).forEach(m=>{
        const li = document.createElement('li');
        li.innerHTML = `<div>${m.vendor}</div><div>Fast · ${m.speed_kw || 0} kW · <b>${m.count || 0}</b></div>`;
        chargerListEl.appendChild(li);
      });
    }

    // actions
    const navBtn = document.getElementById('act_nav');
    const callBtn = document.getElementById('act_call');
    const webBtn = document.getElementById('act_web');
    
    if (navBtn && summary.maps_url) {
      navBtn.addEventListener('click', ()=>{ location.href = summary.maps_url; });
    }
    if (callBtn && summary.phone) {
      callBtn.addEventListener('click', ()=>{ location.href = `tel:${summary.phone}`; });
    }
    if (webBtn && summary.website) {
      webBtn.addEventListener('click', ()=>{ window.open(summary.website, '_blank'); });
    }
  }

  function renderNearby(nearby){
    const root = document.getElementById('nearby-places');
    if (!root) return;
    root.innerHTML = '';
    (nearby.places || []).forEach(p=>{
      const el = document.createElement('div');
      el.className = 'card';
      el.innerHTML = `
        <div class="card__img" style="background-image:url('${p.photo || ''}'); background-size:cover;background-position:center;"></div>
        <div class="card__body">
          <div class="title" style="font-weight:800">${p.name}</div>
          <div class="rating"><span class="star">★</span>${p.rating.toFixed(1)}<span class="src">${p.source || ''}</span></div>
        </div>`;
      root.appendChild(el);
    });
  }

  function renderPlaceActivity(feed){
    const ul = document.getElementById('place-activity');
    if (!ul) return;
    ul.innerHTML = '';
    (feed.items || []).slice(0,6).forEach(it=>{
      const li = document.createElement('li');
      li.innerHTML = `<span class="who">${it.user}</span> charged <span class="kwh">${it.kwh} kWh</span> · +$${(it.earned||0).toFixed(2)}<br>
                      <span class="subtle">${new Date(it.ts).toLocaleString()} · ${it.hub_name}</span>`;
      ul.appendChild(li);
    });
  }

  async function hydratePlacePanel(lat, lng, hub_id='hub_domain_A'){
    const [summary, nearby, feed] = await Promise.all([
      fetchHubSummary(lat,lng), fetchNearbyPlaces(lat,lng), fetchPlaceActivity(hub_id)
    ]);
    renderHubSummary(summary);
    renderNearby(nearby);
    renderPlaceActivity(feed);
  }

  // Bottom sheet snapping (simple)
  (function initSheet(){
    const sheet = document.getElementById('place-sheet');
    if (!sheet) return;
    let startY = 0, startTop = 0;
    const onMove = (e)=>{
      const y = (e.touches ? e.touches[0].clientY : e.clientY);
      const dy = y - startY;
      sheet.style.transform = `translateY(${Math.max(0, Math.min(420, startTop + dy))}px)`;
    };
    const onEnd = ()=>{
      const current = parseInt(sheet.style.transform.replace(/[^\d.]/g,'') || '0', 10);
      const snap = current > 240 ? 420 : (current > 100 ? 200 : 0);
      sheet.style.transition = 'transform 220ms ease';
      sheet.style.transform = `translateY(${snap}px)`;
      setTimeout(()=> sheet.style.transition = '', 240);
    };
    sheet.addEventListener('touchstart', e=>{ startY = e.touches[0].clientY; startTop = parseInt(sheet.style.transform.replace(/[^\d.]/g,'')||'0',10); }, {passive:true});
    sheet.addEventListener('mousedown',   e=>{ startY = e.clientY; startTop = parseInt(sheet.style.transform.replace(/[^\d.]/g,'')||'0',10); });
    sheet.addEventListener('touchmove', onMove, {passive:true});
    window.addEventListener('mousemove', e=>{ if(e.buttons===1) onMove(e); });
    sheet.addEventListener('touchend', onEnd, {passive:true});
    window.addEventListener('mouseup', onEnd);
  })();

  // ==== Community Activity Feed ====
  const FOLLOW_KEY = 'nerava_following';
  function getFollowing(){ try { return JSON.parse(localStorage.getItem(FOLLOW_KEY)||'[]'); } catch { return []; } }
  function setFollowing(list){ localStorage.setItem(FOLLOW_KEY, JSON.stringify(Array.from(new Set(list)))); }

  async function fetchActivityFeed(scope='all', limit=25){
    try{
      const uids = scope==='following' ? getFollowing() : [];
      const qs = new URLSearchParams({ limit:String(limit), following: uids.join(',') });
      const r = await fetch('/v1/social/feed?'+qs.toString());
      if (!r.ok) throw new Error('feed_failed');
      return await r.json();
    }catch{ return []; }
  }

  function renderActivityFeed(items){
    const ul = document.getElementById('activityFeed');
    if (!ul) return;
    ul.innerHTML = '';
    items.forEach(it=>{
      const li = document.createElement('li');
      li.className = 'feed-item';
      li.innerHTML = `
        <div class="avatar"><img alt="" src="${it.avatar_url||'/app/img/avatar-default.svg'}" style="width:100%;height:100%;object-fit:cover"/></div>
        <div class="meta">
          <div class="line1">${it.user_display} charged <strong>${it.kwh.toFixed(1)} kWh</strong> at <strong>${it.hub_name}</strong></div>
          <div class="line2">${new Date(it.timestamp).toLocaleString()} • +$${Number(it.reward_usd).toFixed(2)} • ${it.city}</div>
        </div>
        <div class="cta">
          <button class="follow-btn ${getFollowing().includes(it.user_id)?'following':''}" data-uid="${it.user_id}">
            ${getFollowing().includes(it.user_id)?'Following':'Follow'}
          </button>
        </div>
      `;
      ul.appendChild(li);
    });

    ul.querySelectorAll('.follow-btn').forEach(btn=>{
      btn.addEventListener('click', async () => {
        const uid = btn.getAttribute('data-uid');
        const list = getFollowing();
        const isFollowing = list.includes(uid);
        const next = isFollowing ? list.filter(x=>x!==uid) : list.concat(uid);
        setFollowing(next);
        btn.classList.toggle('following', !isFollowing);
        btn.textContent = !isFollowing ? 'Following' : 'Follow';
        // optimistic; can also POST to server:
        fetch('/v1/social/follow', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ user_id:'demo@nerava.app', target_id: uid, follow: !isFollowing })}).catch(()=>{});
      }, {passive:true});
    });
  }

  async function refreshActivity(scope){
    const items = await fetchActivityFeed(scope, 25);
    renderActivityFeed(items);
  }

  // boot
  document.addEventListener('DOMContentLoaded', ()=>{
    wireUI();
    ensureMap();
    // draw a route after map is ready
    setTimeout(()=>{ ensureMap(); drawRouteToHub(); }, 500);

    // new: hydrate panel once we have a location (fallback to hub)
    if (navigator.geolocation){
      navigator.geolocation.getCurrentPosition(pos=>{
        hydratePlacePanel(pos.coords.latitude, pos.coords.longitude);
      }, _=>{
        hydratePlacePanel(30.4022, -97.7249);
      }, { enableHighAccuracy:true, timeout:3000 });
    } else {
      hydratePlacePanel(30.4022, -97.7249);
    }
    
    // Initialize charging flow
    refreshRewardPreview();
    refreshIncentiveBanner();
    updateStreakDisplay();
    updateCumulativeDisplay(); // Initialize cumulative kWh display
    setInterval(refreshRewardPreview, 30000);
    setInterval(refreshIncentiveBanner, 30000);

    wireChargeHandlers();
    syncChargeUI();

    // Community feed setup
    const feedAllBtn = document.getElementById('feedAllBtn');
    const feedFollowingBtn = document.getElementById('feedFollowingBtn');
    let currentFeedScope = 'all';
    if (feedAllBtn && feedFollowingBtn){
      feedAllBtn.addEventListener('click', ()=>{ currentFeedScope='all'; feedAllBtn.classList.add('active'); feedFollowingBtn.classList.remove('active'); refreshActivity(currentFeedScope); });
      feedFollowingBtn.addEventListener('click', ()=>{ currentFeedScope='following'; feedFollowingBtn.classList.add('active'); feedAllBtn.classList.remove('active'); refreshActivity(currentFeedScope); });
    }
    refreshActivity(currentFeedScope);
    setInterval(()=>refreshActivity(currentFeedScope), 30000);

    // Checkbox interaction polish
    document.querySelectorAll('input[type=checkbox].pref-toggle').forEach(cb=>{
      cb.classList.add('checkbox-pop');
      cb.addEventListener('change', ()=>{
        cb.classList.add('pop');
        setTimeout(()=>cb.classList.remove('pop'), 120);
      }, {passive:true});
    });

    // If you have bottom nav, hook into it so we refresh when switching tabs:
    const nav = document.getElementById('bottom-nav');
    if (nav) nav.addEventListener('click', () => setTimeout(() => {
      refreshRewardPreview();
      refreshIncentiveBanner();
      updateStreakDisplay();
    }, 80));
  });
})();

