#!/bin/sh
set -eu
UI="ui-mobile"

cp "$UI/index.html" "$UI/index.html.bak.inline" 2>/dev/null || true
cp "$UI/styles.css" "$UI/styles.css.bak.inline" 2>/dev/null || true

# 1) Brand text = white
grep -q "/* inline-brand-white */" "$UI/styles.css" 2>/dev/null || cat >> "$UI/styles.css" <<'CSS'
/* inline-brand-white */
.app-header .brand, .brand, .brand-title, .header-wordmark { color:#fff !important; }
.app-header .bolt-mark svg *, .bolt-mark svg * { fill:#fff !important; }
CSS

# 2) Inject inline script just before </body>
if ! grep -q "INLINE_HOTPATCH_NERAVA" "$UI/index.html" ; then
  perl -0777 -pe 's@</body>@<script id="inline-hotpatch" data-tag="INLINE_HOTPATCH_NERAVA">\n(()=>{const RX=/\\bhub_[a-z0-9]+_[a-z0-9]+\\b/gi;function scrub(r=document){r.querySelectorAll(\"*\").forEach(e=>{const t=(e.textContent||\"\").trim();if(t&&t.replace(RX,\"\").trim()===\"\")e.remove();});const w=document.createTreeWalker(r,NodeFilter.SHOW_TEXT,null,false);const edits=[];while(w.nextNode()){const n=w.currentNode;if(RX.test(n.nodeValue))edits.push(n);}edits.forEach(n=>n.nodeValue=(n.nodeValue||\"\").replace(RX,\"\").replace(/\\s{2,}/g,\" \").trim());}function unify(){const c=document.querySelector(\"#hub-card\")||document.querySelector(\"[class*='card']\");if(!c)return;(c.querySelectorAll(\"a,button\")||[]).forEach(b=>/reserve/i.test(b.textContent||\"\")&&b.remove());const d=[...c.querySelectorAll(\"a,button\")].find(b=>/direction/i.test(b.textContent||\"\"));if(d)d.textContent=\"Navigate\";let name=(c.querySelector(\"[data-hub-name],.hub-title\")?.textContent||\"\").trim();if(!name){const meta=(c.querySelector(\".meta-line, p, span, div\")||{}).textContent||\"\";name=(meta.split(\"•\")[0]||\"\").replace(/recommended/i,\"\").replace(/\\bhub\\b$/i,\"\").trim()||\"Nerava Hub\";}if(!c.querySelector(\".hub-name\")){const host=c.querySelector(\".card-title, h2, .title, .header, .top\")||c;const w=document.createElement(\"div\");w.innerHTML=\"<div class=\\\"hub-subtitle\\\" style=\\\"font-size:14px;font-weight:600;opacity:.85;margin-bottom:4px\\\">Recommended</div><div class=\\\"hub-name\\\" style=\\\"font-size:22px;font-weight:800;margin-bottom:6px\\\"></div>\";host.prepend(w);}const el=c.querySelector(\".hub-name\");if(el)el.textContent=name;scrub(c);}document.querySelectorAll(\".app-header .brand,.brand,.brand-title,.header-wordmark\").forEach(n=>n.style.color=\"#fff\");document.querySelectorAll(\".app-header .bolt-mark svg *\").forEach(n=>n.style.fill=\"#fff\");unify();window.addEventListener(\"load\",()=>{unify();let i=0;const t=setInterval(()=>{unify();if(++i>12)clearInterval(t);},150);});new MutationObserver(unify).observe(document.documentElement,{childList:true,subtree:true});})();\n</script>\n</body>@g' -i "$UI/index.html"
fi

# 3) Cache-bust CSS/JS references so the browser fetches fresh files
ts=$(date +%s)
sed -E -i '' "s|(styles\\.css)(\\?v=[0-9]+)?|\\1?v=$ts|g" "$UI/index.html"
sed -E -i '' "s|(app\\.js)(\\?v=[0-9]+)?|\\1?v=$ts|g" "$UI/index.html"

echo "✅ Inline hotpatch installed."
echo "👉 HARD refresh (Cmd/Ctrl+Shift+R). If a PWA, DevTools → Application → Storage → Clear site data once."
