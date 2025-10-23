#!/usr/bin/env bash
set -euo pipefail

# --- Config ---
UI_DIR="ui-mobile"               # change if your folder name differs
ASSETS_DIR="$UI_DIR/assets"
BACKUP_DIR="$UI_DIR/_backup_$(date +%Y%m%d-%H%M%S)"
APP_VER="$(date +%s)"            # cache-bust

echo "▶ Nerava UI hotfix starting…"
[[ -d "$UI_DIR" ]] || { echo "❌ Can't find $UI_DIR — run this from the repo root."; exit 1; }
mkdir -p "$BACKUP_DIR"
cp -a "$UI_DIR/." "$BACKUP_DIR/"
echo "✔ Backed up current UI to $BACKUP_DIR"

# --- Sanity check assets (logos + icons you told me about) ---
missing=0
for f in starbucks.png cfa.jpeg mcds.png bolt-white.svg nav-explore.svg nav-charge.svg nav-wallet.svg nav-profile.svg ; do
  if [[ ! -f "$ASSETS_DIR/$f" ]]; then
    echo "⚠ $ASSETS_DIR/$f not found (UI still works; add when convenient)."
    missing=1
  fi
done
[[ "$missing" == 0 ]] && echo "✔ Required assets found"

# --- Write index.html (complete) ---
cat > "$UI_DIR/index.html" <<'HTML'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Nerava</title>

    <link rel="icon" href="./assets/icon-192.png" />

    <!-- Leaflet CSS (kept above our CSS so overrides work) -->
    <link rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha512-sA+e2OXl2BksZP9m5wI1v1bt3vZ3rZrXQxU+q5eA3cQ8avTwZ7b8qM7OEk6c9MZlJ/zlZuj8C38HE1zVdLrF6g=="
          crossorigin="anonymous"/>

    <link rel="stylesheet" href="./style.css?v=__APP_VER__" />
  </head>
  <body>
    <!-- Top bar -->
    <header class="topbar">
      <div class="logo-wrap">
        <span class="logo-text">NERAVA</span>
        <img class="logo-icon" src="./assets/bolt-white.svg" alt="bolt"/>
      </div>
    </header>

    <!-- Explore-only banner -->
    <section id="incentive-banner" class="banner hidden">
      <span class="bolt">⚡</span>
      <span id="banner-text">Cheaper charging now</span>
    </section>

    <!-- Map is always present; content layers float above -->
    <div id="map"></div>

    <!-- Hub recommendation card -->
    <div id="hub-card" class="card">
      <h1 class="hub-title">Nerava Hub</h1>
      <div class="hub-subtitle">Recommended</div>

      <div class="hub-chips">
        <span class="chip" id="chip-free">3 free</span>
        <span class="chip chip-alt" id="chip-cheap">10% cheaper</span>
      </div>

      <div class="hub-logos">
        <img src="./assets/starbucks.png" alt="Starbucks"/>
        <img src="./assets/cfa.jpeg" alt="Chick-fil-A"/>
        <img src="./assets/mcds.png" alt="McDonald's"/>
      </div>

      <div class="hub-meta">
        <span id="meta-free">3 free</span>
        <span class="dot">•</span>
        <span id="meta-where">Domain, Austin</span>
      </div>

      <button id="navigate" class="cta">Navigate</button>
    </div>

    <!-- Bottom nav -->
    <nav class="navbar">
      <button class="nav-item active" data-tab="explore">
        <img src="./assets/nav-explore.svg" alt="Explore"/><span>Explore</span>
      </button>
      <button class="nav-item" data-tab="charge">
        <img src="./assets/nav-charge.svg" alt="Charge"/><span>Charge</span>
      </button>
      <button class="nav-item" data-tab="wallet">
        <img src="./assets/nav-wallet.svg" alt="Wallet"/><span>Wallet</span>
      </button>
      <button class="nav-item" data-tab="profile">
        <img src="./assets/nav-profile.svg" alt="Profile"/><span>Profile</span>
      </button>
    </nav>

    <!-- Leaflet JS before our app -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
            integrity="sha512-p6uV3FzLrC6YpJdKCu5/3eOq7uXzY8P84l6Xnqv9ZbA0Tg3lD5B1G3+F8E8LDR0qU6cbvhkQhQ3+G7jd3spg=="
            crossorigin="anonymous"></script>

    <script src="./app.js?v=__APP_VER__"></script>
  </body>
</html>
HTML

# --- Write style.css (complete) ---
cat > "$UI_DIR/style.css" <<'CSS'
:root{
  --bg:#0e1a24;
  --card:#0f2233;
  --nav:#0d1c29;
  --text:#e9f2f7;
  --muted:#b6c6d1;
  --chip:#132c40;
  --chip-alt:#20354a;
  --accent:#69d485;
  --navy:#0c2131;
}
*{box-sizing:border-box}
html,body{height:100%;margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,Roboto,Inter,Helvetica,Arial,sans-serif}
img{display:inline-block}

.topbar{position:fixed;top:0;left:0;right:0;height:56px;background:#0b1a28;display:flex;align-items:center;z-index:1000;padding:0 16px}
.logo-wrap{margin:0 auto;display:flex;align-items:center;gap:12px}
.logo-text{letter-spacing:.28em;font-weight:800;color:#fff;font-size:20px}
.logo-icon{height:20px;filter:drop-shadow(0 0 0 rgba(0,0,0,0))}

.banner{position:fixed;top:56px;left:0;right:0;background:#72df8e;color:#0b1a28;font-weight:800;text-align:center;padding:12px 0;z-index:900}
.banner .bolt{margin-right:8px}
.hidden{display:none}

#map{position:fixed;inset:0 0 72px 0; /* leave space for nav */ z-index:100}
.leaflet-container{background:#061018}

.card{
  position:fixed;left:16px;right:16px;bottom:88px;
  background:var(--card);border-radius:28px;padding:20px 20px 16px;
  box-shadow:0 12px 40px rgba(0,0,0,.35);z-index:800
}
.hub-title{margin:0 0 4px;font-size:32px;line-height:1.15;font-weight:900;letter-spacing:.01em}
.hub-subtitle{color:var(--muted);margin-bottom:10px;font-weight:700}
.hub-chips{display:flex;gap:10px;margin-bottom:12px}
.chip{background:var(--chip);padding:8px 12px;border-radius:14px;color:#cfe6f1;font-weight:700;font-size:14px}
.chip-alt{background:var(--chip-alt)}
.hub-logos{display:flex;gap:14px;margin:6px 0 10px}
.hub-logos img{width:42px;height:42px;border-radius:50%;object-fit:cover;box-shadow:0 4px 10px rgba(0,0,0,.35)}
.hub-meta{display:flex;align-items:center;gap:10px;color:#cfe6f1;margin-bottom:14px}
.dot{opacity:.5}
.cta{
  width:100%;border:none;border-radius:18px;background:var(--accent);color:#0d1b16;
  font-weight:900;font-size:20px;padding:16px 18px;cursor:pointer
}

.navbar{
  position:fixed;bottom:0;left:0;right:0;height:72px;background:var(--nav);display:flex;
  align-items:center;justify-content:space-around;z-index:1100;border-top:1px solid rgba(255,255,255,.06)
}
.nav-item{background:transparent;border:none;color:var(--muted);display:flex;flex-direction:column;align-items:center;gap:6px;padding:8px 10px}
.nav-item img{width:24px;height:24px;opacity:.9}
.nav-item.active span{color:#fff}
.nav-item span{font-size:14px;font-weight:700}
CSS

# --- Write app.js (complete) ---
cat > "$UI_DIR/app.js" <<'JS'
/* Nerava UI bootstrap — keeps map visible, card polished, banner only on Explore */

(function () {
  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  const NAV = {
    active: 'explore',   // explore | charge | wallet | profile
    set(tab){
      NAV.active = tab;
      $$('.nav-item').forEach(btn => btn.classList.toggle('active', btn.dataset.tab===tab));
      // Banner only on Explore
      $('#incentive-banner')?.classList.toggle('hidden', tab!=='explore');
      // The map/card are our explore surface; other tabs later can mount panels
      // For now, we keep the map always visible (so no extra work here).
    }
  };

  // --- Map (Leaflet) ---
  let map;
  function initMap() {
    if (typeof L === 'undefined') {
      console.error('Leaflet not loaded');
      return;
    }
    if ($('#map').dataset.ready) return; // idempotent
    map = L.map('map', { zoomControl:false }).setView([30.4025, -97.7258], 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:'&copy; OpenStreetMap contributors'
    }).addTo(map);
    $('#map').dataset.ready = '1';
  }

  // --- Hub Card population (safe defaults) ---
  function populateHubCard() {
    const title = $('.hub-title');
    const sub   = $('.hub-subtitle');
    const chipF = $('#chip-free');
    const chipC = $('#chip-cheap');
    const metaF = $('#meta-free');
    const metaW = $('#meta-where');

    if (title) title.textContent = 'Nerava Hub';
    if (sub)   sub.textContent   = 'Recommended';
    if (chipF) chipF.textContent = '3 free';
    if (chipC) chipC.textContent = '10% cheaper';
    if (metaF) metaF.textContent = '3 free';
    if (metaW) metaW.textContent = 'Domain, Austin';
  }

  // --- Nav wiring ---
  function wireNav() {
    $$('.nav-item').forEach(btn => {
      btn.addEventListener('click', () => NAV.set(btn.dataset.tab));
    });
    NAV.set('explore');
  }

  // --- CTA ---
  function wireCTA() {
    $('#navigate')?.addEventListener('click', () => {
      // Simple directions deeplink stub; insert real lat/lng when desired
      const lat = 30.4025, lng = -97.7258;
      const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
      window.open(url, '_blank');
    });
  }

  // --- Incentive banner text (simple live hint; can call backend later) ---
  function showBannerNow() {
    const banner = $('#incentive-banner');
    if (!banner) return;
    // You can flip this to “in 2 hours” based on /v1/incentives/window when available.
    $('#banner-text').textContent = 'Cheaper charging now';
    banner.classList.remove('hidden');
  }

  // --- Boot ---
  window.addEventListener('DOMContentLoaded', () => {
    initMap();
    populateHubCard();
    wireNav();
    wireCTA();
    showBannerNow();
  });
})();
JS

# --- Replace cache busters ---
sed -i '' "s/__APP_VER__/$APP_VER/g" "$UI_DIR/index.html"

echo "✔ Files written (index.html, style.css, app.js)"
echo "▶ Tips:"
echo "  1) Start a static server in $UI_DIR (examples):"
echo "       cd $UI_DIR && python3 -m http.server 5173"
echo "     then open  http://127.0.0.1:5173"
echo "  2) HARD refresh (Cmd/Ctrl+Shift+R). If you installed as a PWA, remove the SW once."
echo "  3) If you still see old UI, your dev server may have cached output; restart it."
echo "✅ Done."
