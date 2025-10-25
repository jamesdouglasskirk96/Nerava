import { apiGet } from '../core/api.js';
import { ensureMap } from '../app.js';
import { setTab } from '../app.js';

const $ = (s, r=document) => r.querySelector(s);

// Prefer local asset; will fallback to Clearbit if it fails to load.
const STARBUCKS_LOGO_LOCAL = "./img/brands/starbucks.png";
const STARBUCKS_LOGO_CDN   = "https://logo.clearbit.com/starbucks.com";

const _fallbackDeal = {
  merchant: {
    name: "Starbucks",
    address: "310 E 5th St, Austin, TX",
    logo: STARBUCKS_LOGO_LOCAL
  },
  blurb: "Free coffee 2–4pm • 3 min walk"
};

function _bindPerk(deal=_fallbackDeal) {
  const $ = (sel)=>document.querySelector(sel);
  $("#perk-title").textContent   = deal.merchant?.name || "Starbucks";
  $("#perk-address").textContent = deal.merchant?.address || "310 E 5th St, Austin, TX";
  $("#perk-sub").textContent     = deal.blurb || "Free coffee 2–4pm • 3 min walk";

  const logoEl = $("#perk-logo");
  if (logoEl) {
    const primary = deal.merchant?.logo || STARBUCKS_LOGO_LOCAL;
    logoEl.src = primary;

    // Fallback if the primary (local) fails
    logoEl.onerror = () => {
      if (logoEl.dataset.fallback !== "1") {
        logoEl.dataset.fallback = "1";
        logoEl.src = STARBUCKS_LOGO_CDN;
      }
    };
    // Ensure containment styling applies even if external image loads
    logoEl.decoding = "async";
    logoEl.loading = "lazy";
    logoEl.alt = deal.merchant?.name || "Starbucks";
  }

              // Ensure CTA has correct classes and behavior
              const cta = document.getElementById('perk-cta');
              if (cta) {
                cta.classList.add('btn', 'btn-primary', 'btn-wide');
                cta.onclick = () => setTab('charge'); // existing helper
              }
  $("#view-more")?.addEventListener("click", ()=> window.openPerksList?.());
}

export async function initExplore(){
  const map = await ensureMap();          // uses existing map initializer
  setTimeout(() => map.invalidateSize(), 0);

  // Fit to any existing route bounds if available; otherwise default city view
  if (window.lastBounds){
    map.fitBounds(window.lastBounds, { padding:[20,20] });
  } else {
    map.setView([30.2672, -97.7431], 14);
  }

  // Populate perk card with API data or fallback
  try {
    const [hub, deals] = await Promise.all([
      apiGet("/v1/hubs/recommend").catch(()=>null),
      apiGet("/v1/deals/nearby").catch(()=>null)
    ]);
    const deal = deals?.[0] || _fallbackDeal;
    _bindPerk(deal);
  } catch {
    _bindPerk(_fallbackDeal);
  }

  // Make sure the map card never overlaps content
  const card = $('.map-card');
  if (card){ card.style.zIndex = 0; }
}