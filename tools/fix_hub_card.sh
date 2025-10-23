#!/bin/sh
set -eu

UI="ui-mobile"

# backups
cp "$UI/app.js"     "$UI/app.js.bak.hubfix"     2>/dev/null || true
cp "$UI/styles.css" "$UI/styles.css.bak.hubfix" 2>/dev/null || true

# CSS: small subtitle + large name (only appended once)
grep -q "#hub-card .hub-name" "$UI/styles.css" 2>/dev/null || cat >> "$UI/styles.css" <<'CSS'

/* --- Hub card title polish --- */
#hub-card .hub-subtitle{font-size:14px;font-weight:600;opacity:.85;margin-bottom:4px;letter-spacing:.2px}
#hub-card .hub-name{font-size:28px;line-height:1.06;font-weight:800;letter-spacing:.2px;margin-bottom:8px;word-break:break-word}
#hub-card .meta-line{font-size:15px;opacity:.95;display:flex;gap:8px;align-items:baseline;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#hub-card .logo-row{display:flex;gap:12px;flex-wrap:nowrap;margin:8px 0 6px}
#hub-card .logo-row img{width:40px;height:40px;border-radius:999px;object-fit:cover}
CSS

# JS: id scrubber + title builder (appended once)
grep -q "NERAVA_HUB_CARD_FIX" "$UI/app.js" 2>/dev/null || cat >> "$UI/app.js" <<'JS'
// NERAVA_HUB_CARD_FIX — robustly hide hub ids and build clean header
(() => {
  const HUB_ID_RX = /\bhub_[a-z0-9]+_[a-z0-9]+\b/gi;

  function stripHubIdsIn(el) {
    // 1) remove any text-node matches
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false);
    const edits = [];
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (HUB_ID_RX.test(node.nodeValue)) edits.push(node);
    }
    edits.forEach(n => {
      n.nodeValue = (n.nodeValue || "").replace(HUB_ID_RX, "").replace(/\s{2,}/g, " ").trim();
    });

    // 2) hide elements explicitly carrying hub ids (defensive)
    el.querySelectorAll('[data-hub-id], .hub-id, [id*="hub_"], [class*="hub_"]').forEach(x => {
      const txt = (x.textContent || "").toLowerCase();
      if (HUB_ID_RX.test(txt)) x.remove(); // remove instead of hide to avoid layout gaps
    });
  }

  function first(el, sels) {
    for (const s of sels) { const n = el.querySelector(s); if (n) return n; }
    return null;
  }

  function buildCleanHeader(card) {
    // Choose a host spot for the header
    const headerHost = first(card, ['.card-title','h2','.title','.header','.top']) || card;

    // Derive a hub name (prefer data / explicit title)
    let hubName = (first(card, ['[data-hub-name]','.hub-title'])?.textContent || "").trim();
    if (!hubName) {
      // Try to parse from the first meta-ish line, before any "•"
      const metaLike = first(card, ['.meta-line','p','span','div']);
      const rawHead  = (metaLike?.textContent || headerHost.textContent || "").trim();
      const cut      = rawHead.split('•').map(s => s.trim());
      // Keep a reasonable, human-looking piece
      hubName = cut.find(s => s && !/^(0\s*free|premium|standard|tier|busy|open)$/i.test(s)) || "Nerava Hub";
      hubName = hubName.replace(/^\s*recommended\s*/i,'').replace(/\s*\bhub\b\s*$/i,'').trim() || "Nerava Hub";
    }

    // Inject subtitle + big name once
    if (!card.querySelector('.hub-name')) {
      const wrap = document.createElement('div');
      wrap.innerHTML = `
        <div class="hub-subtitle">Recommended</div>
        <div class="hub-name"></div>
      `;
      headerHost.prepend(wrap);
    }
    const nameEl = card.querySelector('.hub-name');
    if (nameEl) nameEl.textContent = hubName;
  }

  function tagMetaLine(card) {
    if (card.querySelector('.meta-line')) return;
    const candidates = Array.from(card.querySelectorAll('p, div, span'))
      .filter(n => /free/i.test(n.textContent) || /premium|standard|tier/i.test(n.textContent));
    if (candidates[0]) candidates[0].classList.add('meta-line');
  }

  function polishCard() {
    const card = document.getElementById('hub-card');
    if (!card) return;
    buildCleanHeader(card);
    tagMetaLine(card);
    stripHubIdsIn(card);
  }

  // Run on load, after small delay, and on any DOM changes
  window.addEventListener('load', () => {
    polishCard();
    // short burst sweeps in case async render paints late
    let n = 0;
    const t = setInterval(() => { polishCard(); if (++n > 12) clearInterval(t); }, 150);
  });
  const mo = new MutationObserver(polishCard);
  mo.observe(document.documentElement, {childList:true,subtree:true});
})();
JS

echo "✅ Hub card fix installed. Do a HARD refresh (Cmd/Ctrl + Shift + R). If using a PWA, clear SW cache once."
