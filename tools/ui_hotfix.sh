#!/bin/sh
set -eu

UI="ui-mobile"

# Backups (first run only)
cp "$UI/app.js"         "$UI/app.js.bak.uihotfix"         2>/dev/null || true
cp "$UI/styles.css"     "$UI/styles.css.bak.uihotfix"     2>/dev/null || true
cp "$UI/index.html"     "$UI/index.html.bak.uihotfix"     2>/dev/null || true

#############################
# 1) Brand wordmark = white #
#############################
# Adds/overrides styles to make the top-left "NERAVA" text white (and slightly brighter than nav items)
grep -q "/* uihotfix-brand */" "$UI/styles.css" 2>/dev/null || cat >> "$UI/styles.css" <<'CSS'
/* uihotfix-brand */
.app-header .brand,
.brand,
.brand-title,
.header-wordmark {
  color: #ffffff !important;
  text-shadow: 0 0 0 rgba(0,0,0,0.01);
  letter-spacing: 0.04em;
}
.app-header .bolt-mark svg path,
.app-header .bolt-mark svg use,
.app-header .bolt-mark svg * {
  fill: #ffffff !important;
}
CSS

#########################################################
# 2) One-button nav on the hub card + scrub hub IDs     #
#########################################################
# Appends a tiny helper at end of app.js (idempotent)
grep -q "NERAVA_UI_HOTFIX" "$UI/app.js" 2>/dev/null || cat >> "$UI/app.js" <<'JS'
// NERAVA_UI_HOTFIX: unify buttons + scrub hub ids + SW cleanup
(() => {
  const HUB_ID_RX = /\bhub_[a-z0-9]+_[a-z0-9]+\b/gi;

  function scrubIds(root){
    if(!root) return;
    // Remove nodes whose text is only the id
    root.querySelectorAll('*').forEach(el=>{
      const t=(el.textContent||'').trim();
      if (t && t.replace(HUB_ID_RX,'').trim()==='') el.remove();
    });
    // Scrub text nodes
    const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,null,false);
    const edits=[];
    while(w.nextNode()){
      const n=w.currentNode;
      if(HUB_ID_RX.test(n.nodeValue)) edits.push(n);
    }
    edits.forEach(n=>{
      n.nodeValue=(n.nodeValue||'').replace(HUB_ID_RX,'').replace(/\s{2,}/g,' ').trim();
    });
    // Clean dangling bullets
    root.querySelectorAll('.meta-line, p, span, div').forEach(n=>{
      const s=(n.textContent||'').replace(/\s*•\s*(?:•\s*)+/g,' • ').replace(/^\s*•\s*|\s*•\s*$/g,'').trim();
      if(s && s!==n.textContent) n.textContent=s;
    });
  }

  function ensureHeader(card){
    if(!card) return;
    const host = card.querySelector('.card-title, h2, .title, .header, .top') || card;
    // Try to get a human hub name
    let name = (card.querySelector('[data-hub-name], .hub-title')?.textContent||'').trim();
    if(!name){
      const meta = card.querySelector('.meta-line, p, span, div');
      const raw  = (meta?.textContent || host.textContent || '').trim();
      name = raw.split('•').map(s=>s.trim())
        .find(s => s && !/^(0\s*free|free|busy|open|premium|standard|tier)$/i.test(s)) || 'Nerava Hub';
      name = name.replace(/^\s*recommended\s*/i,'').replace(/\bhub\b$/i,'').trim() || 'Nerava Hub';
    }
    if(!card.querySelector('.hub-name')){
      const wrap=document.createElement('div');
      wrap.innerHTML = '<div class="hub-subtitle" style="font-size:14px;font-weight:600;opacity:.85;margin-bottom:4px">Recommended</div><div class="hub-name" style="font-size:26px;line-height:1.1;font-weight:800;letter-spacing:.2px;margin-bottom:6px"></div>';
      host.prepend(wrap);
    }
    const el=card.querySelector('.hub-name');
    if(el) el.textContent=name;
  }

  function unifyButtons(card){
    if(!card) return;
    const btns=[...card.querySelectorAll('a,button')];
    const dir = btns.find(b=>/direction/i.test(b.textContent||''));
    // Remove any Reserve button
    btns.forEach(b=>{ if(/reserve/i.test(b.textContent||'')) b.remove(); });
    if(dir){
      dir.textContent='Navigate';
      dir.classList.add('nav-btn');
      if(!dir.parentElement.classList.contains('cta-row')) dir.parentElement.classList.add('cta-row');
    }
  }

  function polish(){
    const card=document.getElementById('hub-card');
    if(card){
      ensureHeader(card);
      unifyButtons(card);
      scrubIds(card);
    }
  }

  // Run now + later (in case async render)
  polish();
  window.addEventListener('load', ()=>{
    polish();
    let i=0; const t=setInterval(()=>{polish(); if(++i>15) clearInterval(t);}, 120);
  });
  new MutationObserver(polish).observe(document.documentElement,{subtree:true,childList:true});

  // Try to evict old service workers (dev convenience)
  if('serviceWorker' in navigator){
    navigator.serviceWorker.getRegistrations().then(rs=>{
      rs.forEach(r=>r.unregister().catch(()=>{}));
    }).catch(()=>{});
  }
})();
JS

# Minimal styles for the single button (append once)
grep -q "/* uihotfix-cta */" "$UI/styles.css" 2>/dev/null || cat >> "$UI/styles.css" <<'CSS'
/* uihotfix-cta */
#hub-card .cta-row{display:flex;gap:14px;align-items:center;flex-wrap:wrap}
#hub-card .nav-btn{padding:.85rem 1.1rem;border-radius:14px;background:#284863;color:#eaf2ff;font-weight:700;display:inline-flex;align-items:center;gap:8px;border:1px solid rgba(255,255,255,.08)}
#hub-card .nav-btn:active{transform:translateY(1px)}
CSS

#############################################
# 3) Cache-bust index links to CSS and JS   #
#############################################
ts=$(date +%s)
# Bust styles.css
sed -E -i '' "s|(styles\.css)(\\?v=[0-9]+)?|\\1?v=$ts|g" "$UI/index.html"
# Bust app.js
sed -E -i '' "s|(app\.js)(\\?v=[0-9]+)?|\\1?v=$ts|g" "$UI/index.html"

echo "✅ UI hotfix installed."
echo "👉 Now do a HARD refresh (Cmd/Ctrl + Shift + R)."
echo "   If you added the app to Home Screen/PWA, open DevTools → Application → Storage → 'Clear site data' once."
