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
  if(tab==='explore') show(banner); else hide(banner);
}

document.querySelectorAll('.tabbar .tab').forEach(b=>{
  b.addEventListener('click',()=>setTab(b.dataset.tab));
});

// ---------- map ----------
let map;
function initMap(lat=30.4021,lng=-97.7265){
  if(map) return;
  map = L.map('map',{ zoomControl:false }).setView([lat,lng], 14);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom: 19, attribution: '&copy; OpenStreetMap'
  }).addTo(map);
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

    // Navigate CTA
    $('#btn-navigate').onclick = () => {
      window.open(
        `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(dest)}`,
        '_blank'
      );
    };

    // Map stays visible under the card
    initMap(rec?.lat || lat, rec?.lng || lng);
    if (map) map.setView([rec?.lat||lat, rec?.lng||lng], 15);
  }catch(e){
    console.warn('recommend error', e);
    initMap(); // keep map visible even if API hiccups
  }
}

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
});
