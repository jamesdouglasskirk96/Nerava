let map, youMarker, targetCircle;
let sessionId = null;
let dwellReq = 60;
let minAcc = 100;

function mmss(s){ const m = Math.floor(s/60), ss = s%60; return `${String(m).padStart(2,'0')}:${String(ss).padStart(2,'0')}` }

function setProgress(sec){
  const pct = Math.min(100, Math.round((sec/dwellReq)*100));
  document.getElementById('progress').style.width = pct+'%';
  document.getElementById('dwell').textContent = mmss(sec);
}

async function start(lat,lng,acc){
  const ua = navigator.userAgent;
  const res = await fetch('/v1/sessions/verify/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:TOKEN,lat,lng,accuracy_m:acc,ua})});
  if(!res.ok){ document.getElementById('status').textContent = 'Link invalid or expired.'; return; }
  const data = await res.json();
  sessionId = data.session_id; dwellReq = data.dwell_required_s; minAcc = data.min_accuracy_m;
  document.getElementById('status').textContent = 'Session active. Stay inside the circle for 1 minute.';
  if(data.target){
    document.getElementById('target').textContent = `${data.target.type==='event'?'Event':'Nearest'}: ${data.target.name}`;
    drawTarget(data.target.lat, data.target.lng, data.target.radius_m);
  } else {
    document.getElementById('target').textContent = 'No target detected yet.';
  }
}

async function doPing(lat,lng,acc){
  const res = await fetch('/v1/sessions/verify/ping',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,lat,lng,accuracy_m:acc})});
  if(!res.ok) return;
  const data = await res.json();
  if(data.reason==='accuracy'){
    document.getElementById('accuracy').textContent = `Accuracy too low. Move to open area (<= ${minAcc}m).`;
  } else {
    document.getElementById('accuracy').textContent = `Accuracy: ~${Math.round(acc)}m`;
  }
  if(data.distance_m !== undefined){
    document.getElementById('inout').textContent = data.distance_m <= 120 ? '✔ in radius' : `~${Math.round(data.distance_m)}m away`;
  }
  if(data.dwell_seconds !== undefined){ setProgress(data.dwell_seconds); }
  if(data.verified){
    document.getElementById('status').textContent = 'Verified! Wallet credited.';
    document.getElementById('cta').style.display = '';
    document.getElementById('perk').onclick = ()=>{ window.location.href = `/v1/gpt/find_merchants?lat=${youMarker.getLatLng().lat}&lng=${youMarker.getLatLng().lng}&category=coffee`; };
    document.getElementById('share').onclick = async ()=>{ try{ await navigator.clipboard.writeText('I just earned with Nerava!'); alert('Copied'); }catch(e){} };
  }
}

function drawTarget(lat,lng,radius){
  if(targetCircle){ targetCircle.remove(); }
  targetCircle = L.circle([lat,lng], {radius, color:'#2b8a3e', fillOpacity:0.1}).addTo(map);
}

function ensureMap(lat,lng){
  if(!map){
    map = L.map('map').setView([lat,lng], 16);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19}).addTo(map);
  }
  if(!youMarker){ youMarker = L.marker([lat,lng]).addTo(map); } else { youMarker.setLatLng([lat,lng]); }
}

async function boot(){
  if(!navigator.geolocation){ document.getElementById('status').textContent = 'Geolocation not supported.'; return; }
  navigator.geolocation.getCurrentPosition(async pos=>{
    const {latitude, longitude, accuracy} = pos.coords;
    ensureMap(latitude, longitude);
    await start(latitude, longitude, accuracy);
    // watch position
    let lastPing = 0;
    navigator.geolocation.watchPosition(async p=>{
      const now = Date.now(); if(now - lastPing < 2000) return; lastPing = now;
      const {latitude:lat, longitude:lng, accuracy:acc} = p.coords;
      ensureMap(lat,lng);
      await doPing(lat,lng,acc);
    }, err=>{}, {enableHighAccuracy:true, maximumAge:1000});
  }, err=>{
    document.getElementById('status').textContent = 'Location permission needed to verify.';
  }, {enableHighAccuracy:true, timeout:10000});
}

boot();


