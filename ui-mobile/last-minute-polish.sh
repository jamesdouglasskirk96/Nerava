#!/usr/bin/env bash
set -euo pipefail

UI_DIR="ui-mobile"
ASSETS="$UI_DIR/assets"

# sanity
mkdir -p "$ASSETS"

# Warn if brand/seed logos are missing (won't fail the build)
for f in starbucks.png cfa.jpeg mcds.png nerava-mark.svg bolt-white.svg nav-explore.svg nav-charge.svg nav-wallet.svg nav-profile.svg; do
  if [[ ! -f "$ASSETS/$f" ]]; then
    echo "WARN: $ASSETS/$f not found. (UI will still work; add later for best look.)"
  fi
done

# ------------------------------
# index.html
# ------------------------------
if [[ -f "$UI_DIR/index.html" ]]; then cp "$UI_DIR/index.html" "$UI_DIR/index.html.bak"; fi
cat > "$UI_DIR/index.html" <<'HTML'
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
  <title>Nerava</title>
  <link rel="icon" href="./assets/icon-192.png" />
  <link rel="stylesheet" href="./styles.css" />
</head>
<body>
  <!-- Brand bar -->
  <header id="brandbar" class="brand">
    <div class="brand__wrap">
      <img class="brand__word" src="./assets/nerava-mark.svg" alt="NERAVA" />
      <img class="brand__bolt" src="./assets/bolt-white.svg" alt="⚡" />
    </div>
  </header>

  <!-- Explore-only banner -->
  <div id="incentiveBanner" class="banner banner--hidden">
    <span class="banner__icon">⚡</span>
    <span class="banner__text">Cheaper charging now</span>
  </div>

  <!-- MAP (fixed background) -->
  <div id="map"></div>

  <!-- Bottom card: Recommended hub -->
  <section id="hubCard" class="card card--bottom">
    <div class="card__title-row">
      <h2 class="card__title">Recommended hub</h2>
      <div class="chip-row">
        <span id="chipBusy" class="chip">busy</span>
        <span id="chipTier" class="chip">premium</span>
      </div>
    </div>
    <div class="merchant-badges">
      <img src="./assets/starbucks.png" alt="Starbucks" />
      <img src="./assets/cfa.jpeg" alt="Chick-fil-A" />
      <img src="./assets/mcds.png" alt="McDonald's" />
    </div>
    <div id="hubMeta" class="muted">0 free • Nerava Hub • 0</div>
    <div class="cta-row">
      <button id="reserveBtn" class="btn btn--primary">Reserve</button>
      <button id="dirBtn" class="btn btn--ghost">Directions</button>
    </div>
  </section>

  <!-- Plan Trip panel (hidden by default) -->
  <section id="tripPanel" class="card card--bottom card--hidden">
    <h2 class="card__title">Plan a Trip</h2>
    <p class="muted">Enter a destination, we’ll suggest a hub along the way.</p>
    <div class="trip-row">
      <input id="tripInput" class="input" placeholder="e.g., 401 Congress Ave, Austin" />
      <button id="tripGo" class="btn btn--ghost">Plan</button>
    </div>
  </section>

  <!-- Floating Plan-a-Trip button -->
  <button id="planFab" class="fab" aria-label="Plan a Trip">Plan a Trip</button>

  <!-- Bottom nav -->
  <nav class="tabbar">
    <button class="tab active" data-tab="explore">
      <img src="./assets/nav-explore.svg" alt="" />
      <span>Explore</span>
    </button>
    <button class="tab" data-tab="charge">
      <img src="./assets/nav-charge.svg" alt="" />
      <span>Charge</span>
    </button>
    <button class="tab" data-tab="wallet">
      <img src="./assets/nav-wallet.svg" alt="" />
      <span>Wallet</span>
    </button>
    <button class="tab" data-tab="profile">
      <img src="./assets/nav-profile.svg" alt="" />
      <span>Profile</span>
    </button>
  </nav>

  <!-- Page containers (one visible at a time besides map/bg) -->
  <main id="pages">
    <section id="page-explore" class="page page--visible"><!-- hubCard lives over this --></section>

    <section id="page-charge" class="page">
      <div class="card">
        <h2 class="card__title">Charge</h2>
        <p class="muted">Scan a QR on-site or view your current session details (coming soon).</p>
      </div>
    </section>

    <section id="page-wallet" class="page">
      <div class="card">
        <h2 class="card__title">Wallet</h2>
        <div id="walletTotal" class="wallet-total">$0.00</div>
        <h3 class="section-head">Ways you earned</h3>
        <div id="walletList" class="wallet-list"></div>
      </div>
    </section>

    <section id="page-profile" class="page">
      <div class="card">
        <h2 class="card__title">Profile</h2>
        <div class="muted">Signed in as <span id="profileEmail">demo@nerava.app</span></div>
        <div class="prefs">
          <label><input type="checkbox" data-pref="pref_coffee"> Coffee & Bakery</label>
          <label><input type="checkbox" data-pref="pref_food"> Quick Bites</label>
          <label><input type="checkbox" data-pref="pref_dog"> Dog Friendly</label>
          <label><input type="checkbox" data-pref="pref_kid"> Kid Friendly</label>
          <label><input type="checkbox" data-pref="pref_shopping"> Shopping</label>
          <label><input type="checkbox" data-pref="pref_exercise"> Exercise</label>
        </div>
        <div class="cta-row">
          <button id="savePrefs" class="btn btn--primary">Save Preferences</button>
          <button id="refreshRec" class="btn btn--ghost">See New Recommendation</button>
        </div>
      </div>
    </section>
  </main>

  <script src="./app.js" type="module"></script>
</body>
</html>
HTML

# ------------------------------
# styles.css
# ------------------------------
if [[ -f "$UI_DIR/styles.css" ]]; then cp "$UI_DIR/styles.css" "$UI_DIR/styles.css.bak"; fi
cat > "$UI_DIR/styles.css" <<'CSS'
:root{
  --bg:#0b1220;
  --panel:#0f1a2b;
  --ink:#e9f0ff;
  --muted:#b9c3d9;
  --chip:#1b2a44;
  --green:#42d07f;
  --navy:#091529;  /* brand bar */
  --brand:#0b2a45; /* darker navy for banner row */
}
*{box-sizing:border-box}
html,body{height:100%}
body{
  margin:0;
  font-family: ui-sans-serif,system-ui,Segoe UI,Roboto,Helvetica,Arial,Apple Color Emoji,Segoe UI Emoji;
  background:var(--bg);
  color:var(--ink);
}

/* brand */
.brand{position:fixed;top:0;left:0;right:0;height:64px;background:var(--navy);z-index:10;display:flex;align-items:center;justify-content:center}
.brand__wrap{display:flex;align-items:center;gap:14px}
.brand__word{height:24px;opacity:.92;filter: brightness(0) saturate(100%) invert(9%) sepia(12%) saturate(1936%) hue-rotate(174deg) brightness(94%) contrast(94%)} /* navy tint on dark bg */
.brand__bolt{height:22px;filter:none}

/* banner */
.banner{position:fixed;top:64px;left:0;right:0;height:44px;background:#63db8f;color:#04240f;display:flex;align-items:center;justify-content:center;gap:10px;font-weight:800;z-index:9}
.banner__icon{filter: brightness(0) saturate(100%) invert(26%) sepia(75%) saturate(512%) hue-rotate(88deg) brightness(93%) contrast(95%)}
.banner--hidden{display:none}

/* map stays behind everything */
#map{position:fixed;top:108px;left:0;right:0;bottom:80px;z-index:0}

/* pages area (empty container that provides scroll when needed) */
#pages{position:relative;z-index:1;padding-top:108px;padding-bottom:110px}

/* cards */
.card{background:var(--panel);border-radius:22px;padding:18px 20px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.card--bottom{position:fixed;left:16px;right:16px;bottom:96px;z-index:2}
.card--hidden{display:none}
.card__title{margin:0 0 10px 0;font-size:24px;font-weight:900}
.card__title-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.muted{color:var(--muted)}
.chip-row{display:flex;gap:10px}
.chip{background:var(--chip);color:#bcd1f3;padding:6px 10px;border-radius:16px;font-size:.85rem;text-transform:lowercase}

/* merchant badges (seeded logos) */
.merchant-badges{display:flex;gap:12px;margin:10px 0 6px}
.merchant-badges img{width:36px;height:36px;border-radius:18px;object-fit:cover;background:#08111f}

/* inputs & buttons */
.input{flex:1;background:#0a1627;border:1px solid #16263f;color:var(--ink);border-radius:12px;padding:12px 14px;font-size:16px}
.btn{border:0;border-radius:14px;padding:12px 16px;font-weight:800}
.btn--primary{background:var(--green);color:#052016}
.btn--ghost{background:#101d31;color:#cfe2ff;border:1px solid #1d2d49}
.cta-row{display:flex;gap:12px;margin-top:12px}

.trip-row{display:flex;gap:10px}

/* fab */
.fab{position:fixed;right:20px;bottom:170px;z-index:3;background:#13243e;color:#d9e8ff;border:1px solid #284369;padding:12px 16px;border-radius:999px;font-weight:800}

/* pages visibility */
.page{display:none;padding:16px}
.page--visible{display:block}

/* tabbar */
.tabbar{position:fixed;left:0;right:0;bottom:0;height:80px;background:rgba(4,10,20,.92);backdrop-filter: blur(8px);display:flex;align-items:center;justify-content:space-around;z-index:5;border-top:1px solid #13233b}
.tab{display:flex;flex-direction:column;align-items:center;gap:6px;background:transparent;color:#c7d8f7;border:0}
.tab img{width:26px;height:26px;opacity:.9}
.tab.active{color:#fff}
.tab.active img{opacity:1}

/* wallet */
.wallet-total{font-size:36px;font-weight:900;margin:10px 0 8px}
.section-head{margin:6px 0 8px;font-size:16px;color:#cbd8f5;font-weight:800}
.wallet-list{max-height:60vh;overflow:auto;border-top:1px solid #1b2a44}
.wallet-item{display:flex;align-items:center;justify-content:space-between;padding:12px 4px;border-bottom:1px solid #13233b}
CSS

# ------------------------------
# app.js
# ------------------------------
if [[ -f "$UI_DIR/app.js" ]]; then cp "$UI_DIR/app.js" "$UI_DIR/app.js.bak"; fi
cat > "$UI_DIR/app.js" <<'JS'
/* Nerava UI glue (vanilla) */
const BASE = localStorage.getItem("NERAVA_URL") || "http://127.0.0.1:8000";
const USER = localStorage.getItem("NERAVA_USER") || "demo@nerava.app";

// elements
const pages = {
  explore: document.getElementById("page-explore"),
  charge : document.getElementById("page-charge"),
  wallet : document.getElementById("page-wallet"),
  profile: document.getElementById("page-profile")
};
const tabs = [...document.querySelectorAll(".tabbar .tab")];
const banner = document.getElementById("incentiveBanner");
const hubCard = document.getElementById("hubCard");
const tripPanel = document.getElementById("tripPanel");
const planFab = document.getElementById("planFab");
const hubMeta = document.getElementById("hubMeta");
const chipBusy = document.getElementById("chipBusy");
const chipTier = document.getElementById("chipTier");
const walletTotal = document.getElementById("walletTotal");
const walletList = document.getElementById("walletList");
const profileEmail = document.getElementById("profileEmail");

// brand-centered banner text already in CSS

// map
let map, userLat = 30.4021, userLng = -97.7265;
function initMap(){
  // lazy import leaflet from CDN (no build step)
  const link = document.createElement('link');
  link.rel = "stylesheet";
  link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
  document.head.appendChild(link);
  const s = document.createElement('script');
  s.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
  s.onload = () => {
    map = L.map('map',{zoomControl:false}).setView([userLat, userLng], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19}).addTo(map);
  };
  document.body.appendChild(s);
}

// helpers
async function jget(path, params={}){
  const url = new URL(BASE + path);
  Object.entries(params).forEach(([k,v])=> url.searchParams.set(k,v));
  const r = await fetch(url.toString());
  if(!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}
async function jpost(path, body){
  const r = await fetch(BASE + path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body||{})});
  if(!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

// Explore load
async function refreshRecommendation(){
  // get nearby hubs and recommend (backend already implements)
  const hubs = await jget("/v1/hubs/nearby",{lat:userLat,lng:userLng,radius_km:2,max_results:5});
  const rec  = await jget("/v1/hubs/recommend",{lat:userLat,lng:userLng,radius_km:2,user_id:USER});
  // decorate chip/meta
  chipBusy.textContent = (rec.status || "open");
  chipTier.textContent = (rec.tier || "premium").toLowerCase();
  const hubName = rec.name || (hubs[0]?.name ?? "Nerava Hub • ?");
  const free = rec.free_ports ?? hubs[0]?.free_ports ?? 0;
  hubMeta.textContent = `${free} free • ${hubName}`;
  // keep card visible
  hubCard.classList.remove("card--hidden");
}

// Trip toggle
planFab.addEventListener("click", ()=>{
  const showingTrip = !tripPanel.classList.contains("card--hidden");
  if(showingTrip){
    // hide trip, show hub card
    tripPanel.classList.add("card--hidden");
    hubCard.classList.remove("card--hidden");
    planFab.textContent = "Plan a Trip";
  }else{
    // show trip, hide hub card
    tripPanel.classList.remove("card--hidden");
    hubCard.classList.add("card--hidden");
    planFab.textContent = "Close";
  }
});

// Banner only on Explore
function setTab(tab){
  tabs.forEach(t=>t.classList.toggle("active", t.dataset.tab===tab));
  Object.entries(pages).forEach(([k,el])=>{
    el.classList.toggle("page--visible", k===tab);
  });
  if(tab==="explore"){ banner.classList.remove("banner--hidden"); }
  else { banner.classList.add("banner--hidden"); }
}
tabs.forEach(t=> t.addEventListener("click", ()=> setTab(t.dataset.tab)));

// Profile prefs save/refresh
profileEmail.textContent = USER;
document.getElementById("savePrefs").addEventListener("click",async ()=>{
  const checks = [...document.querySelectorAll('[data-pref]')];
  const payload = Object.fromEntries(checks.map(c=>[c.dataset.pref, c.checked]));
  await jpost(`/v1/users/${encodeURIComponent(USER)}/prefs`, payload);
  await refreshRecommendation();
});
document.getElementById("refreshRec").addEventListener("click", refreshRecommendation);

// Wallet: total + non-zero entries only
async function loadWallet(){
  const bal = await jget("/v1/wallet",{user_id:USER});
  const cents = bal.balance_cents ?? 0;
  walletTotal.textContent = (cents>=0? '+$' : '-$') + (Math.abs(cents)/100).toFixed(2);

  // try /history; if not present, synthesize from credit/debits if you have them stored later
  let items=[];
  try{
    items = await jget("/v1/wallet/history",{user_id:USER});
  }catch{ items=[]; }
  walletList.innerHTML = "";
  for(const it of (items||[])){
    const a = (it.amount_cents ?? 0);
    if(Math.abs(a) < 1) continue; // hide zero noise
    const el = document.createElement("div");
    el.className = "wallet-item";
    const label = (it.type || "ADJUST").replace(/_/g,' ');
    const money = (a>=0? '+$' : '-$') + (Math.abs(a)/100).toFixed(2);
    el.innerHTML = `<div>${label}</div><div>${money}</div>`;
    walletList.appendChild(el);
  }
}

// Incentive banner content (if your backend has it; otherwise default text remains)
async function maybeBanner(){
  try{
    const w = await jget("/v1/incentives/window");
    // expect: { status: "now"|"soon"|"none", starts_in_min?: number }
    const txt = w.status==="now" ? "Cheaper charging now"
              : w.status==="soon" ? `Cheaper charging in ${w.starts_in_min} min`
              : null;
    if(txt){ document.querySelector(".banner__text").textContent = txt; }
  }catch{ /* ignore */ }
}

// Init
window.addEventListener("load", async ()=>{
  initMap();
  setTab("explore");
  await Promise.all([refreshRecommendation(), loadWallet(), maybeBanner()]);
});
JS

echo "OK — UI files written."
