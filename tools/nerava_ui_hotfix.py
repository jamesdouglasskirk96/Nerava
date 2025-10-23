# tools/nerava_ui_hotfix.py
from pathlib import Path
import re, time

ROOT = Path(__file__).resolve().parents[1]
UI   = ROOT / "ui-mobile"
idx  = UI / "index.html"
css  = UI / "styles.css"

if not idx.exists():
    raise SystemExit(f"❌ Not found: {idx}")

# Backups
ts = int(time.time())
for p in (idx, css):
    if p.exists():
        p.with_suffix(p.suffix + f".bak.{ts}").write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

# Append brand → white CSS
css_txt = css.read_text(encoding="utf-8") if css.exists() else ""
if "/* nerava-hotfix-brand */" not in css_txt:
    css_txt += """
/* nerava-hotfix-brand */
.app-header .brand, .brand, .brand-title, .header-wordmark { color:#fff !important; }
.app-header .bolt-mark svg *, .bolt-mark svg * { fill:#fff !important; }
"""
    css.write_text(css_txt, encoding="utf-8")

html = idx.read_text(encoding="utf-8")

# Inline hotpatch script (use function replacement so backslashes are not parsed)
payload = r"""
<script id="nerava-inline-hotpatch" data-tag="NERAVA_INLINE_HOTPATCH">
(()=>{const RX=/\bhub_[a-z0-9]+_[a-z0-9]+\b/gi;
function scrubText(root){
  const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,null,false);let n,eds=[];
  while((n=w.nextNode())){ if(RX.test(n.nodeValue)) eds.push(n); }
  eds.forEach(n=>{ n.nodeValue=(n.nodeValue||"").replace(RX,"").replace(/\s{2,}/g," ").trim(); });
}
function unify(){
  document.querySelectorAll(".app-header .brand,.brand,.brand-title,.header-wordmark").forEach(el=>el.style.color="#fff");
  document.querySelectorAll(".app-header .bolt-mark svg *").forEach(n=>n.style.fill="#fff");

  const card=document.getElementById("hub-card")
    || document.querySelector('[data-hub-card]')
    || [...document.querySelectorAll(".card, [class*='card']")].find(c=>/recommended/i.test(c.textContent||""))
    || null;
  if(!card){ return; }

  // collapse to single Navigate button
  const actions=[...card.querySelectorAll("a,button")];
  let nav=actions.find(b=>/direction|navigate/i.test(b.textContent||""));
  if(!nav) nav=actions[0];
  if(nav){
    nav.textContent="Navigate";
    actions.forEach(b=>{ if(b!==nav && /reserve|direction/i.test((b.textContent||"").toLowerCase())) b.remove(); });
  }

  // header (subtitle + name)
  const host = card.querySelector(".card-title, h2, .title, .header, .top") || card;
  if(!card.querySelector(".hub-name")){
    const wrap=document.createElement("div");
    wrap.innerHTML='<div class="hub-subtitle" style="font-size:14px;font-weight:600;opacity:.85;margin-bottom:4px">Recommended</div><div class="hub-name" style="font-size:22px;font-weight:800;margin-bottom:6px"></div>';
    host.prepend(wrap);
  }
  const nameEl=card.querySelector(".hub-name");
  if(nameEl){
    let name=(card.querySelector("[data-hub-name], .hub-title")?.textContent||"").trim();
    if(!name){
      const meta = card.querySelector(".meta-line, p, span, div");
      if(meta){
        const raw=(meta.textContent||"").replace(RX,"");
        const parts=raw.split("•").map(s=>s.trim()).filter(Boolean);
        name = parts.find(s=>!/^(0\s*free|free|busy|open|premium|standard|tier)$/i.test(s)) || "Nerava Hub";
        name = name.replace(/^recommended\s*/i,"").replace(/\bhub\b$/i,"").trim() || "Nerava Hub";
      } else { name="Nerava Hub"; }
    }
    nameEl.textContent=name;
  }

  scrubText(card); // remove hub_dyn_* anywhere
}
unify();
window.addEventListener("load", ()=>{ unify(); let i=0; const t=setInterval(()=>{unify(); if(++i>10) clearInterval(t);},150); });
new MutationObserver(unify).observe(document.documentElement,{childList:true,subtree:true});
})();
</script>
"""

if "nerava-inline-hotpatch" not in html:
    # insert before </body> using a function replacement
    html = re.sub(r"</body\s*>", lambda m: payload + "\n" + m.group(0), html, flags=re.I|re.S, count=1)

# Cache-bust links so browser fetches fresh files
stamp = str(ts)
html = re.sub(r'(styles\.css)(\?v=\d+)?', r'\1?v='+stamp, html)
html = re.sub(r'(app\.js)(\?v=\d+)?', r'\1?v='+stamp, html)

idx.write_text(html, encoding="utf-8")
print("✅ Hotfix written. HARD refresh (Cmd/Ctrl+Shift+R). In DevTools → Network, tick “Disable cache”. If installed as PWA, clear site data once.")
