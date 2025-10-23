(() => {
  const HUB = { name:'Nerava Hub', lat:30.4022, lng:-97.7249, city:'Domain, Austin' };

  const $  = (id)=>document.getElementById(id);
  const on = (el, ev, fn)=>el && el.addEventListener(ev, fn, {passive:true});

  function setActive(tabName){
    // tabs
    ['Explore','Charge','Wallet','Profile'].forEach(n=>{
      const btn = $('tab'+n);
      if(btn) btn.classList.toggle('active', n===tabName);
    });
    // pages
    ['Explore','Charge','Wallet','Profile'].forEach(n=>{
      const pg = $('page'+n);
      if(pg) pg.classList.toggle('active', n===tabName);
    });
    // banner only on Explore
    const banner = $('dealBanner');
    if(banner) banner.style.display = (tabName==='Explore') ? '' : 'none';
  }

  // Map & route
  let map, routingCtl;
  function ensureMap(){
    if(typeof L==='undefined'){ setTimeout(ensureMap,120); return; }
    if(map) return;
    map = L.map('map',{ zoomControl:false });
    map.setView([HUB.lat, HUB.lng], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      {maxZoom:19, attribution:'&copy; OpenStreetMap'}).addTo(map);

    // Hub marker
    L.circleMarker([HUB.lat, HUB.lng], {radius:8, color:'#55ffc7', weight:4, fill:true, fillOpacity:.5})
      .addTo(map).bindPopup(HUB.name);
  }

  function drawRouteToHub(){
    if(typeof L==='undefined' || !map || !L.Routing){ return; }

    // Remove prior route
    if(routingCtl){ map.removeControl(routingCtl); routingCtl = null; }

    const fallbackStart = [30.3982,-97.7239]; // a nearby point if geolocation denied

    const makeControl = (start) => {
      routingCtl = L.Routing.control({
        waypoints: [ L.latLng(start[0],start[1]), L.latLng(HUB.lat,HUB.lng) ],
        routeWhileDragging:false,
        addWaypoints:false,
        draggableWaypoints:false,
        fitSelectedRoutes:true,
        show:false
      }).addTo(map);
    };

    if(navigator.geolocation){
      navigator.geolocation.getCurrentPosition(
        pos => makeControl([pos.coords.latitude, pos.coords.longitude]),
        _err => makeControl(fallbackStart),
        {enableHighAccuracy:true, maximumAge:60000, timeout:4000}
      );
    } else {
      makeControl(fallbackStart);
    }
  }

  function wireUI(){
    // Tabs
    on($('tabExplore'),'click', ()=>setActive('Explore'));
    on($('tabCharge'), 'click', ()=>setActive('Charge'));
    on($('tabWallet'), 'click', ()=>setActive('Wallet'));
    on($('tabProfile'),'click', ()=>setActive('Profile'));

    // Charge here -> go to Charge page
    on($('chargeHereBtn'),'click', ()=>{
      setActive('Charge');
    });
  }

  // boot
  document.addEventListener('DOMContentLoaded', ()=>{
    wireUI();
    ensureMap();
    // draw a route after map is ready
    setTimeout(()=>{ ensureMap(); drawRouteToHub(); }, 500);
  });
})();
