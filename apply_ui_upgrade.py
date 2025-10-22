#!/usr/bin/env python3
import os, sys, shutil, datetime

ROOT = os.path.abspath(os.getcwd())
UI_DIR = os.path.join(ROOT, "ui-mobile")
INDEX = os.path.join(UI_DIR, "index.html")
CSS   = os.path.join(UI_DIR, "css", "style.css")
JS    = os.path.join(UI_DIR, "js", "app.js")

NEW_INDEX = r"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"/>
    <title>Nerava</title>
    <link rel="manifest" href="manifest.json"/>
    <link rel="stylesheet" href="css/style.css"/>
    <script>
      // Configure your backend origin here if needed
      window.NERAVA_BASE  = window.NERAVA_BASE  || (location.origin.includes('127.0.0.1') ? 'http://127.0.0.1:8000' : location.origin);
      window.NERAVA_USER  = window.NERAVA_USER  || 'demo@nerava.app';
      window.NERAVA_PREFS = window.NERAVA_PREFS || (localStorage.getItem('NERAVA_PREFS') || 'coffee_bakery,quick_bite');
    </script>
    <link rel="icon" href="assets/icon-192.png"/>
  </head>
  <body>
    <div class="topbar">
      <div class="brand">Nerava</div>
      <div class="spacer"></div>
    </div>

    <!-- Incentive banner (hidden unless an off-peak window is active) -->
    <div id="incentive-banner" class="banner hidden">Cheaper charging now</div>

    <div id="map"></div>

    <!-- Recommended hub card -->
    <div id="recommend-card" class="card hidden">
      <div class="card-row">
        <div class="card-title" id="rec-name">Recommended hub</div>
        <div class="pill" id="rec-status">open</div>
      </div>
      <div class="card-sub" id="rec-sub">2 free • PREMIUM</div>
      <div class="card-row logos" id="merchant-strip"></div>
      <div class="card-row">
        <button id="btn-reserve" class="btn btn-primary">Reserve</button>
        <button id="btn-directions" class="btn btn-ghost">Directions</button>
      </div>
    </div>

    <!-- VIEW: Plan a Charge (QR + current session) -->
    <section id="view-plan-charge" class="view hidden">
      <div class="card">
        <div class="card-title">Charge</div>
        <div class="card-sub">Scan station QR or view your current session.</div>
        <div class="card-row">
          <button id="btn-scan" class="btn btn-primary">Scan QR</button>
          <button id="btn-session" class="btn btn-ghost">View Session</button>
        </div>
        <div id="session-info" class="mt"></div>
        <video id="qr-video" class="hidden" playsinline></video>
        <canvas id="qr-canvas" class="hidden"></canvas>
      </div>
    </section>

    <!-- VIEW: Plan a Trip (placeholder) -->
    <section id="view-plan-trip" class="view hidden">
      <div class="card">
        <div class="card-title">Plan a Trip</div>
        <div class="card-sub">Multi-stop planning coming soon—today we focus on hubs & perks.</div>
      </div>
    </section>

    <!-- VIEW: Wallet -->
    <section id="view-wallet" class="view hidden">
      <div class="card">
        <div class="card-row">
          <div class="card-title">Wallet</div>
          <div class="pill" id="wallet-balance">—</div>
        </div>
        <div id="wallet-history" class="list"></div>
      </div>
    </section>

    <!-- VIEW: Profile -->
    <section id="view-profile" class="view hidden">
      <div class="card">
        <div class="card-title">Profile</div>
        <div class="card-sub">Signed in as <span id="profile-email"></span></div>
        <div class="grid prefs">
          <label><input type="checkbox" id="pref_coffee"> Coffee & Bakery</label>
          <label><input type="checkbox" id="pref_food"> Quick Bites</label>
          <label><input type="checkbox" id="pref_dog"> Dog Friendly</label>
          <label><input type="checkbox" id="pref_kid"> Kid Friendly</label>
          <label><input type="checkbox" id="pref_shopping"> Shopping</label>
          <label><input type="checkbox" id="pref_exercise"> Exercise</label>
        </div>
        <div class="card-row">
          <button id="btn-save-prefs" class="btn btn-primary">Save Preferences</button>
          <button id="btn-recommend-refresh" class="btn btn-ghost">See New Recommendation</button>
        </div>
        <div id="prefs-impact" class="mt muted"></div>
      </div>
    </section>

    <nav class="bottombar">
      <button class="navbtn active" data-view="home"><span>Plan a Charge</span></button>
      <button class="navbtn" data-view="plan-trip"><span>Plan a Trip</span></button>
      <button class="navbtn" data-view="plan-charge"><span>Charge</span></button>
      <button class="navbtn" data-view="wallet"><span>Wallet</span></button>
      <button class="navbtn" data-view="profile"><span>Profile</span></button>
    </nav>

    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="js/app.js"></script>
  </body>
</html>
"""

NEW_CSS = r"""/* Base */
:root{
  --bg:#0b0f14;
  --fg:#ffffff;
  --muted:#9fb1c6;
  --card:#121821;
  --accent:#17e6a1;
}
*{ box-sizing:border-box; }
html,body{ margin:0; padding:0; background:var(--bg); color:var(--fg); font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'SF Pro Text', Roboto, Segoe UI, Arial, sans-serif; }
a{ color:var(--fg); text-decoration:none; }

.topbar{ position:fixed; top:0; left:0; right:0; height:56px; display:flex; align-items:center; padding:0 14px; background:rgba(10,14,18,0.8); backdrop-filter: blur(6px); border-bottom:1px solid rgba(255,255,255,.06); z-index:10; }
.brand{ font-weight:800; letter-spacing:.3px; }
.spacer{ flex:1; }

#map{ position:fixed; top:56px; bottom:64px; left:0; right:0; }

.card{ position:fixed; left:12px; right:12px; bottom:84px; padding:12px; background:var(--card); border:1px solid rgba(255,255,255,.08); border-radius:14px; box-shadow: 0 10px 30px rgba(0,0,0,.35); }
.card-title{ font-weight:800; }
.card-sub{ color:var(--muted); margin-top:4px; }
.card-row{ display:flex; align-items:center; justify-content:space-between; margin-top:10px; gap:10px; }
.card-row.logos img{ width:36px; height:36px; border-radius:18px; margin-right:8px; object-fit:cover; }
.btn{ padding:10px 14px; border-radius:10px; font-weight:600; cursor:pointer; }
.btn-primary{ background:#17e6a1; color:#053; }
.btn-ghost{ background:transparent; border:1px solid rgba(255,255,255,.12); color:#fff; }
.pill{ background:rgba(255,255,255,.08); padding:6px 10px; border-radius:999px; }

/* Bottom nav */
.bottombar{ position:fixed; left:0; right:0; bottom:0; height:64px; display:flex; align-items:center; justify-content:space-around; background:rgba(10,14,18,0.9); border-top:1px solid rgba(255,255,255,.06); z-index:10; }
.navbtn{ appearance:none; border:none; background:transparent; color:#9fb1c6; font-weight:600; border-radius:12px; padding:8px 12px; }
.navbtn.active{ color:#fff; background:rgba(255,255,255,.06); }

/* New helpers */
.view.hidden{ display:none }
.list{ margin-top:10px; }
.list-item{ padding:10px 0; border-top:1px solid rgba(255,255,255,.06); }
.muted{ color: var(--muted); }
.mt{ margin-top:10px; }
.grid.prefs{ display:grid; grid-template-columns:1fr 1fr; gap:8px 14px; margin-top:10px; }
.banner{ position:fixed; top:56px; left:0; right:0; padding:8px 12px; text-align:center; background:#00e676; color:#063; font-weight:700; z-index:9; }
.banner.warn{ background:#ffde59; color:#1a1a00; }
"""

NEW_JS = r"""const BASE  = window.NERAVA_BASE;
const USER  = window.NERAVA_USER;
let PREFS_CSV = window.NERAVA_PREFS;
let map, userMarker, hubMarker, lastRecBeforePrefs = null;

function $(s){ return document.querySelector(s); }
function el(t, a={}){ const n=document.createElement(t); Object.assign(n,a); return n; }

async function getJSON(path, params={}){
  const url = new URL(path, BASE);
  Object.entries(params).forEach(([k,v]) => url.searchParams.set(k, v));
  const r = await fetch(url.toString());
  if(!r.ok) throw new Error('HTTP '+r.status);
  return r.json();
}
async function postJSON(path, body={}, params={}){
  const url = new URL(path, BASE);
  Object.entries(params).forEach(([k,v]) => url.searchParams.set(k, v));
  const r = await fetch(url.toString(), { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
  if(!r.ok) throw new Error('HTTP '+r.status);
  return r.json();
}

/* ---------------- MAP + HOME ---------------- */
function initMap(lat,lng){
  if(map) return;
  map = L.map('map', {zoomControl:false}).setView([lat,lng], 15);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom: 20}).addTo(map);
  userMarker = L.circleMarker([lat,lng],{radius:6,color:'#9fc1ff'}).addTo(map);
}
function setHubMarker(lat,lng,status){
  if(hubMarker) map.removeLayer(hubMarker);
  const color = status==='open' ? '#2ecc71' : (status==='busy' ? '#ff6b6b' : '#f1c40f');
  hubMarker = L.circleMarker([lat,lng],{radius:10,color}).addTo(map);
}
function formatSub(h){ const n=h.free_ports??0; const tier=(h.tier||'').toUpperCase(); return `${n} free • ${tier}`; }

function merchantLogo(src){ const img=el('img'); img.src = src || 'assets/icon-192.png'; img.alt='m'; return img; }

async function loadHome(){
  let lat=30.4021, lng=-97.7265;
  try{
    await new Promise(res => navigator.geolocation.getCurrentPosition(
      p=>{lat=p.coords.latitude; lng=p.coords.longitude; res();},
      _=>res(), {timeout:1500}
    ));
  }catch(_){}
  initMap(lat,lng);

  // Baseline recommendation (for delta after saving prefs)
  const rec = await getJSON('/v1/hubs/recommend', {lat,lng,radius_km:2,user_id:USER});
  lastRecBeforePrefs = rec;
  if(rec && rec.lat && rec.lng){
    setHubMarker(rec.lat, rec.lng, rec.status||'open');
    $('#rec-name').textContent = rec.name || 'Recommended hub';
    $('#rec-status').textContent = rec.status || 'open';
    $('#rec-sub').textContent = formatSub(rec);
    $('#recommend-card').classList.remove('hidden');

    // Merchants (unified: local perks first + Google)
    const m = await getJSON('/v1/merchants/nearby', {lat:rec.lat, lng:rec.lng, radius_m:600, max_results:20, prefs:PREFS_CSV, hub_id: rec.id||'hub_unknown'});
    const strip = $('#merchant-strip'); strip.innerHTML='';
    m.slice(0,12).forEach(x => strip.appendChild(merchantLogo(x.logo)));

    // Reserve
    $('#btn-reserve').onclick = async ()=>{
      try{
        // Fixed payload: valid start_iso key/value
        const body = {
          hub_id: rec.id || 'hub',
          user_id: USER,
          start_iso: new Date(Date.now()+10*60*1000).toISOString(),
          minutes: 30
        };
        const out = await postJSON('/v1/reservations/soft', body);
        alert('Held: ' + (out.human || `${out.window_start_iso}–${out.window_end_iso}`));
      }catch(e){ alert('Reserve failed'); }
    };
    // Directions
    $('#btn-directions').onclick = ()=>{
      location.href = `https://www.google.com/maps/dir/?api=1&destination=${rec.lat},${rec.lng}`;
    };
  }

  // Incentive banner probe: if award_off_peak returns >0, show "Cheaper charging now"
  try{
    const probe = await postJSON('/v1/incentives/award_off_peak', {}, {user_id: USER});
    const banner = $('#incentive-banner');
    if (probe && (probe.awarded_cents || 0) > 0) {
      banner.textContent = 'Cheaper charging now';
      banner.classList.remove('hidden'); banner.classList.remove('warn');
    } else {
      banner.classList.add('hidden');
    }
  }catch(_){}
}

/* ---------------- WALLET ---------------- */
async function loadWallet(){
  const bal = await getJSON('/v1/wallet', {user_id: USER});
  $('#wallet-balance').textContent = `${(bal.balance_cents||0)/100} USD`;

  try{
    const hist = await getJSON('/v1/wallet/history', {user_id: USER});
    const list = $('#wallet-history'); list.innerHTML='';
    (hist||[]).slice(0,20).forEach(row=>{
      const item = el('div', {className:'list-item'});
      const cents = row.amount_cents ?? row.cents ?? 0;
      const sign = cents >= 0 ? '+' : '−';
      const abs = Math.abs(cents);
      item.textContent = `${row.reason || 'Transaction'} • ${sign}$${(abs/100).toFixed(2)} • ${row.at || row.timestamp || ''}`;
      list.appendChild(item);
    });
  }catch(_){
    $('#wallet-history').innerHTML = '<div class="muted">History not available</div>';
  }
}

/* ---------------- PROFILE (prefs) ---------------- */
function prefsCSVFromForm(){
  const ids = ['pref_coffee','pref_food','pref_dog','pref_kid','pref_shopping','pref_exercise'];
  const map = {}; ids.forEach(id=> map[id] = $('#'+id).checked);
  const pos = [];
  if(map.pref_coffee) pos.push('coffee_bakery');
  if(map.pref_food) pos.push('quick_bite');
  return { json: map, csv: pos.join(',') };
}
async function loadProfile(){
  $('#profile-email').textContent = USER;
  try{
    const current = await getJSON(`/v1/users/${encodeURIComponent(USER)}/prefs`);
    ['pref_coffee','pref_food','pref_dog','pref_kid','pref_shopping','pref_exercise']
      .forEach(k => { if (k in current) $('#'+k).checked = !!current[k]; });
  }catch(_){}

  $('#btn-save-prefs').onclick = async ()=>{
    const { json, csv } = prefsCSVFromForm();
    await postJSON(`/v1/users/${encodeURIComponent(USER)}/prefs`, json);
    PREFS_CSV = csv || PREFS_CSV;
    window.NERAVA_PREFS = PREFS_CSV;
    localStorage.setItem('NERAVA_PREFS', PREFS_CSV);
    alert('Preferences saved');
  };

  $('#btn-recommend-refresh').onclick = async ()=>{
    try{
      const after = await getJSON('/v1/hubs/recommend', {lat:30.4021,lng:-97.7265,radius_km:2,user_id:USER});
      const before = lastRecBeforePrefs || {};
      const added = (after.reason_tags||[]).filter(x => !(before.reason_tags||[]).includes(x));
      const scoreBefore = before.score ?? 0, scoreAfter = after.score ?? 0;
      $('#prefs-impact').innerHTML = `
        <div>Score: ${scoreBefore.toFixed(1)} → ${scoreAfter.toFixed(1)} (${(scoreAfter-scoreBefore).toFixed(1)})</div>
        <div>Reasons added: ${added.join(', ') || '—'}</div>`;
      await loadHome(); // refresh merchants strip with new prefs
    }catch(e){ $('#prefs-impact').textContent = 'Could not refresh recommendation.'; }
  };
}

/* ---------------- PLAN CHARGE (QR placeholder) ---------------- */
async function loadPlanCharge(){
  $('#session-info').innerHTML = '<div class="muted">No active session. Scan a station QR to begin.</div>';
  $('#btn-session').onclick = async ()=>{
    alert('Session details demo coming soon');
  };
  $('#btn-scan').onclick = ()=>{
    alert('QR scanner demo coming soon — will use jsQR/WebRTC.');
  };
}

/* ---------------- SIMPLE ROUTER ---------------- */
function showView(key){
  const views = {
    home:     ()=>{ $('#recommend-card').classList.remove('hidden'); $('#view-plan-charge').classList.add('hidden'); $('#view-plan-trip').classList.add('hidden'); $('#view-wallet').classList.add('hidden'); $('#view-profile').classList.add('hidden'); },
    'plan-charge': ()=>{ $('#recommend-card').classList.add('hidden'); $('#view-plan-charge').classList.remove('hidden'); $('#view-plan-trip').classList.add('hidden'); $('#view-wallet').classList.add('hidden'); $('#view-profile').classList.add('hidden'); loadPlanCharge(); },
    'plan-trip':   ()=>{ $('#recommend-card').classList.add('hidden'); $('#view-plan-charge').classList.add('hidden'); $('#view-plan-trip').classList.remove('hidden'); $('#view-wallet').classList.add('hidden'); $('#view-profile').classList.add('hidden'); },
    wallet:  ()=>{ $('#recommend-card').classList.add('hidden'); $('#view-plan-charge').classList.add('hidden'); $('#view-plan-trip').classList.add('hidden'); $('#view-wallet').classList.remove('hidden'); $('#view-profile').classList.add('hidden'); loadWallet(); },
    profile: ()=>{ $('#recommend-card').classList.add('hidden'); $('#view-plan-charge').classList.add('hidden'); $('#view-plan-trip').classList.add('hidden'); $('#view-wallet').classList.add('hidden'); $('#view-profile').classList.remove('hidden'); loadProfile(); },
  };
  (views[key]||views.home)();
  document.querySelectorAll('.navbtn').forEach(b => b.classList.toggle('active', b.dataset.view===key));
}

/* ---------------- BOOT ---------------- */
document.addEventListener('DOMContentLoaded', async ()=>{
  try{
    const h = await getJSON('/v1/health');
    if(!h.ok) throw new Error('backend not ok');
  }catch(e){
    alert('Backend unavailable at '+BASE);
  }
  await loadHome();
  document.querySelectorAll('.navbtn').forEach(btn => btn.addEventListener('click', ()=> showView(btn.dataset.view)));
});
"""

def ensure_exists(path, kind):
  if not os.path.exists(path):
    print(f"[!] Missing {kind}: {path}")
    sys.exit(1)

def backup(path):
  ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
  bdir = os.path.join(os.path.dirname(path), ".backup")
  os.makedirs(bdir, exist_ok=True)
  bpath = os.path.join(bdir, os.path.basename(path) + f".{ts}.bak")
  shutil.copy2(path, bpath)
  return bpath

def write_file(path, content):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, "w", encoding="utf-8") as f:
    f.write(content)

def main():
  print("== Nerava UI Upgrade (one-shot) ==")
  ensure_exists(UI_DIR, "UI directory")
  ensure_exists(INDEX, "index.html")
  ensure_exists(CSS, "style.css")
  ensure_exists(JS, "app.js")

  b_index = backup(INDEX)
  b_css   = backup(CSS)
  b_js    = backup(JS)

  write_file(INDEX, NEW_INDEX)
  write_file(CSS, NEW_CSS)
  write_file(JS, NEW_JS)

  print("✓ Updated files:")
  print(f"  - {INDEX}  (backup: {b_index})")
  print(f"  - {CSS}    (backup: {b_css})")
  print(f"  - {JS}     (backup: {b_js})")
  print("\nRun the backend and open the UI:\n  uvicorn app.main:app --reload\n  (then open http://127.0.0.1:8000/app if you mounted /app)\n")
  print("Or serve static UI directly:\n  cd ui-mobile && python3 -m http.server 5173  # open http://127.0.0.1:5173\n")

if __name__ == "__main__":
  main()
