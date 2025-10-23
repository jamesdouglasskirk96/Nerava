#!/bin/sh
set -eu

UI="ui-mobile"

# Backups (once)
cp "$UI/app.js"     "$UI/app.js.bak.uipatch"     2>/dev/null || true
cp "$UI/styles.css" "$UI/styles.css.bak.uipatch" 2>/dev/null || true

# Small CSS tweak: spacing for one-button layout (append once)
grep -q "#hub-card .nav-btn" "$UI/styles.css" 2>/dev/null || cat >> "$UI/styles.css" <<'CSS'
/* ---- UI quick patch ---- */
#hub-card .cta-row{display:flex;gap:14px;align-items:center;flex-wrap:wrap}
#hub-card .nav-btn{padding:.85rem 1.1rem;border-radius:14px;background:#284863;color:#e8f1ff;font-weight:700;display:inline-flex;align-items:center;gap:8px;border:1px solid rgba(255,255,255,.08)}
#hub-card .nav-btn:active{transform:translateY(1px)}
CSS

# Robust DOM patch (append once)
grep -q "NERAVA_UI_QUICK_PATCH" "$UI/app.js" 2>/dev/null || cat >> "$UI/app.js" <<'JS'
// NERAVA_UI_QUICK_PATCH — scrub hub ids + unify buttons
(() => {
  const HUB_ID_RX = /\bhub_[a-z0-9]+_[a-z0-9]+\b/gi;

  // text-node scrub + element removal if a node is just the id
  function scrubIds(root){
    if(!root) return;
    // (1) remove elements that are *only* the id
    root.querySelectorAll('*').forEach(el=>{
      const t=(el.textContent||'').trim();
      if (t && t.replace(HUB_ID_RX,'').trim()==='') {
        el.remove();
      }
    });
    // (2) scrub within text nodes
    const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,null,false);
    const edits=[];
    while(w.nextNode()){
      const n=w.currentNode;
      if(HUB_ID_RX.test(n.nodeValue)) edits.push(n);
    }
    edits.forEach(n=>{
      n.nodeValue=(n.nodeValue||'').replace(HUB_ID_RX,'').replace(/\s{2,}/g,' ').trim();
    });
    // (3) clean “ • ” runs that can be left behind
    root.querySelectorAll('.meta-line, p, span, div').forEach(n=>{
      const s=(n.textContent||'').replace(/\s*•\s*(?:•\s*)+/g,' • ').replace(/^\s*•\s*|\s*•\s*$/g,'').trim();
      if(s && s!==n.textContent) n.textContent=s;
    });
  }

  // Make a smaller "Recommended" subtitle and a big hub name
  function ensureHeader(card){
    if(!card) return;
    const headerHost = card.querySelector('.card-title, h2, .title, .header, .top') || card;
    let hubName = (card.querySelector('[data-hub-name], .hub-title')?.textContent||'').trim();
    if(!hubName){
      // Try to infer from any line that contains “Nerava Hub …”
      const meta = card.querySelector('.meta-line, p, span, div');
      const raw = (meta?.textContent || headerHost.textContent || '').trim();
      hubName = raw.split('•').map(s=>s.trim())
        .find(s => s && !/^(0\s*free|free|busy|open|premium|standard|tier)$/i.test(s)) || 'Nerava Hub';
      hubName = hubName.replace(/^\s*recommended\s*/i,'').replace(/\bhub\b$/i,'').trim() || 'Nerava Hub';
    }
    if(!card.querySelector('.hub-name')){
      const wrap=document.createElement('div');
      wrap.innerHTML=`
        <div class="hub-subtitle" style="font-size:14px;font-weight:600;opacity:.85;margin-bottom:4px">Recommended</div>
        <div class="hub-name" style="font-size:26px;line-height:1.1;font-weight:800;letter-spacing:.2px;margin-bottom:6px"></div>
      `;
      headerHost.prepend(wrap);
    }
    const nameEl=card.querySelector('.hub-name');
    if(nameEl) nameEl.textContent=hubName;
  }

  // Collapse Reserve + Directions ⇒ Navigate
  function unifyButtons(card){
    if(!card) return;
    // Find a Directions-like button and make it our single "Navigate"
    const dirBtn=[...card.querySelectorAll('a,button')].find(b=>/direction/i.test(b.textContent||''));
    if(dirBtn){
      dirBtn.textContent='Navigate';
      dirBtn.classList.add('nav-btn');
    }
    // Remove any Reserve buttons to avoid confusion
    [...card.querySelectorAll('a,button')].forEach(b=>{
      if(/reserve/i.test(b.textContent||'')) b.remove();
    });
    // Optional: ensure a container row looks good
    if(dirBtn && !dirBtn.parentElement.classList.contains('cta-row')){
      dirBtn.parentElement.classList.add('cta-row');
    }
  }

  function polish(){
    const card=document.getElementById('hub-card');
    if(!card) return;
    ensureHeader(card);
    scrubIds(card);
    unifyButtons(card);
  }

  // Run now, on load, a short sweep, and on DOM changes
  polish();
  window.addEventListener('load', ()=>{
    polish();
    let n=0; const t=setInterval(()=>{polish(); if(++n>15) clearInterval(t);}, 120);
  });
  const mo=new MutationObserver(polish);
  mo.observe(document.documentElement,{subtree:true,childList:true});
})();
JS

echo "✅ UI quick patch installed (id scrub + 'Navigate' button)."
echo "👉 Hard refresh the app (Cmd/Ctrl+Shift+R). If installed as a PWA, clear site data once."
