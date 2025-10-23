#!/usr/bin/env bash
set -euo pipefail

UI="ui-mobile"

# Backups
cp "$UI/app.js"      "$UI/app.js.bak.title"   2>/dev/null || true
cp "$UI/styles.css"  "$UI/styles.css.bak.title" 2>/dev/null || true

# 1) CSS: readable title/subtitle + robust layout/ellipsis; hide hub_id tokens
cat >> "$UI/styles.css" <<'CSS'

/* ===== Hub card readability & fit ===== */
#hub-card .hub-subtitle {
  font-size: 14px;
  font-weight: 600;
  opacity: 0.85;
  margin-bottom: 4px;
  letter-spacing: .2px;
}
#hub-card .hub-name {
  font-size: 28px;
  line-height: 1.05;
  font-weight: 800;
  letter-spacing: .2px;
  margin-bottom: 8px;
  word-break: break-word;
}
#hub-card .meta-line {
  font-size: 15px;
  opacity: 0.95;
  display: flex;
  gap: 8px;
  align-items: baseline;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
#hub-card .logo-row { display: flex; gap: 12px; flex-wrap: nowrap; margin: 8px 0 6px; }
#hub-card .logo-row img { width: 40px; height: 40px; border-radius: 999px; object-fit: cover; }

/* Hide any hub id tokens like hub_dyn_xxxx wherever they appear in the card */
#hub-card * { unicode-bidi: plaintext; }
CSS

# 2) JS: inject small subtitle + big hub name, and strip hub_id tokens from visible text
cat >> "$UI/app.js" <<'JS'

// ===== Hub Card Title Polish (non-invasive DOM tweak) =====
(() => {
  const HUB_ID_RX = /\bhub_[a-z0-9]+_[a-z0-9]+\b/gi;

  function first(el, sels) {
    for (const s of sels) { const n = el.querySelector(s); if (n) return n; }
    return null;
  }

  function stripIdsIn(el) {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false);
    const toFix = [];
    while (walker.nextNode()) {
      if (HUB_ID_RX.test(walker.currentNode.nodeValue)) toFix.push(walker.currentNode);
    }
    toFix.forEach(n => { n.nodeValue = n.nodeValue.replace(HUB_ID_RX, '').replace(/\s{2,}/g,' ').trim(); });
  }

  function polishCard() {
    const card = document.getElementById('hub-card');
    if (!card) return;

    const headerHost = (card.querySelector('.card-title') || card.querySelector('h2') || card);
    // Try to derive a real hub name
    let hubName = (card.querySelector('[data-hub-name], .hub-title')?.textContent || '').trim();
    if (!hubName) {
      const raw = (headerHost.textContent || '').trim();
      hubName = raw.replace(/recommended\s*/i,'').replace(/\bhub\b$/i,'').trim() || 'Nerava Hub';
    }

    if (!card.querySelector('.hub-name')) {
      const header = document.createElement('div');
      header.innerHTML = `
        <div class="hub-subtitle">Recommended</div>
        <div class="hub-name"></div>
      `;
      headerHost.prepend(header);
    }
    const nameEl = card.querySelector('.hub-name');
    if (nameEl) nameEl.textContent = hubName;

    if (!card.querySelector('.meta-line')) {
      const candidates = Array.from(card.querySelectorAll('p, div, span'))
        .filter(n => /free/i.test(n.textContent) && /Nerava Hub/i.test(n.textContent) || /premium|standard|tier/i.test(n.textContent));
      if (candidates[0]) candidates[0].classList.add('meta-line');
    }

    stripIdsIn(card);
  }

  const mo = new MutationObserver(() => polishCard());
  mo.observe(document.body, { subtree: true, childList: true });
  window.addEventListener('load', polishCard);
})();
JS

echo "✅ Hub title polished. Hard refresh (Cmd/Ctrl + Shift + R)."
