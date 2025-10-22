const BASE  = window.NERAVA_BASE;
const USER  = window.NERAVA_USER;
const PREFS = window.NERAVA_PREFS;
let map, userMarker, hubMarker;

function $(s){ return document.querySelector(s); }
function el(t, a={}){const n=document.createElement(t);Object.assign(n,a);return n;}

async function getJSON(path, params={}){
  const url = new URL(path, BASE);
  Object.entries(params).forEach(([k,v])=> url.searchParams.set(k,v));
  const r = await fetch(url.toString());
  if(!r.ok) throw new Error('HTTP '+r.status);
  return r.json();
}
async function postJSON(path, body={}, params={}){
  const url = new URL(path, BASE);
  Object.entries(params).forEach(([k,v])=> url.searchParams.set(k,v));
  const r = await fetch(url.toString(),{
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)
  });
  if(!r.ok) throw new Error('HTTP '+r.status);
  return r.json();
}

function initMap(lat,lng){
  if(map) return;
  map = L.map('map',{zoomControl:false}).setView([lat,lng],15);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:20}).addTo(map);
  userMarker = L.circleMarker([lat,lng],{radius:6,color:'#9fc1ff'}).addTo(map);
}
function setHubMarker(lat,lng,status){
  if(hubMarker) map.removeLayer(hubMarker);
  const color = status==='open' ? '#2ecc71' : (status==='busy' ? '#ff6b6b' : '#f1c40f');
  hubMarker = L.circleMarker([lat,lng],{radius:10,color}).addTo(map);
}
function formatSub(h){ const n=h.free_ports??0; const tier=(h.tier||'').toUpperCase(); return `${n} free • ${tier}`; }
function merchantLogo(src){ const img=el('img'); img.src=src; img.alt='m'; return img; }

async function load(){
  try{
    let lat=30.4021,lng=-97.7265;
    try{
      await new Promise(res=>navigator.geolocation.getCurrentPosition(
        p=>{lat=p.coords.latitude;lng=p.coords.longitude;res();}, _=>res(), {timeout:2000}
      ));
    }catch(_){}
    initMap(lat,lng);

    // 1) Recommend a hub
    const rec = await getJSON('/v1/hubs/recommend',{lat,lng,radius_km:2,user_id:USER});
    if(rec && rec.lat && rec.lng){
      setHubMarker(rec.lat,rec.lng,rec.status||'open');
      $('#rec-name').textContent = rec.name || 'Recommended hub';
      $('#rec-status').textContent = rec.status || 'open';
      $('#rec-sub').textContent = formatSub(rec);
      $('#recommend-card').classList.remove('hidden');

      // 2) Merchants
      const m = await getJSON('/v1/merchants/nearby',{lat:rec.lat,lng:rec.lng,radius_m:600,max_results:20,prefs:PREFS});
      const strip = $('#merchant-strip'); strip.innerHTML='';
      m.slice(0,12).forEach(x=> strip.appendChild(merchantLogo(x.logo || 'assets/icon-192.png')) );

      // 3) Actions
      $('#btn-reserve').onclick = async ()=>{
        try{
          const body = { hub_id: rec.id || 'hub', user_id: USER, start_iso: new Date(Date.now()+10*60*1000).toISOString(), minutes: 30 };
          const out = await postJSON('/v1/reservations/soft', body);
          alert('Held: ' + (out.human||`${out.window_start_iso}–${out.window_end_iso}`));
        }catch(e){ alert('Reserve failed'); }
      };
      $('#btn-directions').onclick = ()=>{
        location.href = `https://www.google.com/maps/dir/?api=1&destination=${rec.lat},${rec.lng}`;
      };
    }
  }catch(e){
    console.error(e);
    alert('Failed to load UI. Check backend at '+BASE);
  }
}
document.addEventListener('DOMContentLoaded', load);
