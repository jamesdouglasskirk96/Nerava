/* globals L */
const BASE = (localStorage.NERAVA_URL || "http://127.0.0.1:8000");
const USER = (localStorage.NERAVA_USER || "demo@nerava.app");

// ---------- helpers ----------
const $ = sel => document.querySelector(sel);
const show = el => el.classList.remove('hidden');
const hide = el => el.classList.add('hidden');
const fmtMoney = cents => `+$${(Number(cents||0)/100).toFixed(2)}`;
const stripHubIds = s => (s||'').replace(/\bhub_[a-z0-9]+_[a-z0-9]+\b/gi,'').replace(/\s{2,}/g,' ').trim();

// ---------- tabs ----------
const pages = {
  explore: $('#page-explore'),
  charge:  $('#page-charge'),
  wallet:  $('#page-wallet'),
  profile: $('#page-profile'),
};
const banner = $('#incentive-banner');

function setTab(tab){
  Object.entries(pages).forEach(([k,el])=>{
    el.classList.toggle('active', k===tab);
  });
  document.querySelectorAll('.tabbar .tab').forEach(b=>{
    b.classList.toggle('active', b.dataset.tab===tab);
  });
  if(tab==='explore'){ 
    show(banner); 
    try{ map && map.invalidateSize(false); }catch(_){ }
    if(window.lastBounds) fitMapToRoute(window.lastBounds);
  }
  else { hide(banner); }
}

document.querySelectorAll('.tabbar .tab').forEach(b=>{
  b.addEventListener('click',()=>setTab(b.dataset.tab));
});

// ---------- map ----------
let map, walkLayer, chargerMarker, merchantMarker;
function initMap(lat=30.4021,lng=-97.7265){
  if(!map){
    map = L.map('map',{ zoomControl:false });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
      maxZoom: 19, attribution: '&copy; OpenStreetMap'
    }).addTo(map);
  }
  try { map.setView([lat,lng], Math.max(map.getZoom()||14, 14)); } catch(_){}
  requestAnimationFrame(()=>setTimeout(()=>{ try{ map.invalidateSize(false); }catch(_){ } }, 60));
}

function fitMapToRoute(bounds){
  if(!map || !bounds) return;
  try{
    map.fitBounds(bounds, { padding:[60,60], maxZoom:16, animate:true });
    let z = map.getZoom();
    if (z < 13) map.setZoom(13);
    if (z > 17) map.setZoom(17);
    window.lastBounds = bounds;
    const kick = ()=>{ try{ map.invalidateSize(false); window.lastBounds && map.fitBounds(window.lastBounds, { padding:[60,60], maxZoom:16, animate:false }); }catch(_){} };
    requestAnimationFrame(()=>setTimeout(kick, 120));
  }catch(_){}
}

// ---------- data fetch ----------
async function api(path, params){
  const url = new URL(BASE + path);
  Object.entries(params||{}).forEach(([k,v])=>url.searchParams.set(k,v));
  const r = await fetch(url, { headers:{'Accept':'application/json'} });
  if(!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

async function loadBanner(){
  try{
    const data = await api('/v1/incentives/window');
    const txt = data?.active ? "Cheaper charging now"
      : (data?.starts_in_minutes ? `Cheaper charging in ${Math.ceil(data.starts_in_minutes/60)} hours` : "Cheaper charging now");
    $('#banner-text').textContent = txt;
  }catch{ $('#banner-text').textContent = "Cheaper charging now"; }
}

async function loadRecommendation(){
  const lat = 30.4025, lng = -97.7258;
  try{
    const rec = await api('/v1/hubs/recommend', { lat, lng, radius_km:2, user_id:USER });

    // Parse values from API
    let name   = stripHubIds(rec?.name || 'Nerava Hub');
    let free   = Number(rec?.free_ports ?? 0);
    let status = (rec?.status || 'busy').toLowerCase();
    let tier   = (rec?.tier || 'premium').toLowerCase();
    const dest = `${rec?.lat||lat},${rec?.lng||lng}`;

    // ---- DEMO OVERRIDES (requested) ----
    // Force the UI copy for the live demo
    status = 'free';
    const tierText = '10% cheaper';
    free = 3;
    // ------------------------------------

    // Paint UI
    $('#hub-name').textContent   = name;
    $('#hub-short').textContent  = name;
    $('#hub-free').textContent   = `${free} free`;
    $('#hub-status').textContent = status;
    $('#hub-tier').textContent   = tierText;   // show "10% cheaper" instead of "premium"

    // CTA now starts walking route UI if merchant candidate is present (set later)
    $('#btn-navigate').onclick = () => setTab('explore');

    // Ensure map alive
    initMap(rec?.lat || lat, rec?.lng || lng);
  }catch(e){
    console.warn('recommend error', e);
    initMap(); // keep map visible even if API hiccups
  }
}

// Draw a route and fit (used by dual-session code)
window.drawWalkingRoute = async function drawWalkingRoute(charger, merchant){
  if(!charger || !merchant) return;
  initMap(charger.lat, charger.lng);
  if(walkLayer){ try{ walkLayer.remove(); }catch(_){ } }
  if(chargerMarker){ try{ chargerMarker.remove(); }catch(_){ } }
  if(merchantMarker){ try{ merchantMarker.remove(); }catch(_){ } }

  chargerMarker   = L.circleMarker([charger.lat, charger.lng],   {radius:6, color:'#0ea5e9'}).addTo(map);
  merchantMarker  = L.circleMarker([merchant.lat, merchant.lng], {radius:6, color:'#f59e0b'}).addTo(map);

  // try OSRM foot; fallback to straight line
  let poly;
  try{
    const url = `https://router.project-osrm.org/route/v1/foot/${charger.lng},${charger.lat};${merchant.lng},${merchant.lat}?overview=full&geometries=geojson`;
    const r = await fetch(url,{mode:'cors'}); const j = r.ok ? await r.json() : null;
    const coords = j?.routes?.[0]?.geometry?.coordinates?.map(([x,y])=>[y,x]);
    if(coords?.length) poly = L.polyline(coords,{weight:5,opacity:.9});
  }catch(_){}
  if(!poly) poly = L.polyline([[charger.lat,charger.lng],[merchant.lat,merchant.lng]], {dashArray:'6,8', weight:4});
  walkLayer = poly.addTo(map);

  const b = L.latLngBounds([[charger.lat,charger.lng],[merchant.lat,merchant.lng]]);
  fitMapToRoute(b);
  window.lastBounds = b;
};

async function loadWallet(){
  try{
    const bal = await api('/v1/wallet', { user_id: USER });
    $('#wallet-balance').textContent = fmtMoney(bal?.balance_cents || 0);

    const ways = [
      ['Off-peak award', 50],
      ['Perk reward', 75],
      ['Utility bonus', 100]
    ];
    const ul = $('#wallet-ways'); ul.innerHTML = '';
    ways.forEach(([label,cents])=>{
      const li = document.createElement('li');
      li.innerHTML = `<span>${label}</span><strong>${fmtMoney(cents)}</strong>`;
      ul.appendChild(li);
    });
  }catch(e){ console.warn('wallet error', e); }
}

async function loadPrefs(){
  $('#prof-email').textContent = USER;
  try{
    const r = await api(`/v1/users/${encodeURIComponent(USER)}/prefs`);
    $('#p-coffee').checked = !!r.pref_coffee;
    $('#p-quick').checked  = !!r.pref_food;
    $('#p-dog').checked    = !!r.pref_dog;
    $('#p-kid').checked    = !!r.pref_kid;
    $('#p-shop').checked   = !!r.pref_shopping;
    $('#p-ex').checked     = !!r.pref_exercise;
  }catch{}
}

async function savePrefs(){
  const payload = {
    pref_coffee: $('#p-coffee').checked,
    pref_food:   $('#p-quick').checked,
    pref_dog:    $('#p-dog').checked,
    pref_kid:    $('#p-kid').checked,
    pref_shopping: $('#p-shop').checked,
    pref_exercise:  $('#p-ex').checked,
  };
  try{
    const r = await fetch(`${BASE}/v1/users/${encodeURIComponent(USER)}/prefs`, {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
    });
    if(!r.ok) throw 0;
    alert('Preferences saved.');
  }catch{ alert('Failed to save preferences'); }
}

$('#btn-save-prefs').addEventListener('click', savePrefs);
$('#btn-see-new').addEventListener('click', ()=>{ setTab('explore'); loadRecommendation(); });

// ---------- boot ----------
window.addEventListener('load', async ()=>{
  setTab('explore');
  initMap();
  await loadBanner();
  await loadRecommendation();
  await loadWallet();
  await loadPrefs();
  // keep Leaflet healthy on resize/orientation
  let t; const kick = ()=>{ clearTimeout(t); t=setTimeout(()=>{ try{ map && map.invalidateSize(false); }catch(_){ } }, 120); };
  window.addEventListener('resize', kick, {passive:true});
  window.addEventListener('orientationchange', kick, {passive:true});
});
