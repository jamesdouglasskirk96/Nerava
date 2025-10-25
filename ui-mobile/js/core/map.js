/* globals L */
let _map, _routeLayer, _markers = [];
const MAP_ID = 'map';

export function ensureMap(center=[30.4025,-97.7258], zoom=15){
  const el = document.getElementById(MAP_ID);
  if(!el) return null;
  if (_map) { // idempotent
    setTimeout(()=>_map.invalidateSize(), 0);
    return _map;
  }
  _map = L.map(MAP_ID, { zoomControl:false, attributionControl:false })
    .setView(center, zoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{ maxZoom:19 }).addTo(_map);
  return _map;
}

export function clearRoute(){
  if (_routeLayer){ _map.removeLayer(_routeLayer); _routeLayer = null; }
  _markers.forEach(m => _map.removeLayer(m));
  _markers = [];
}

export function drawRoute(points){ // points: [[lat,lng],[lat,lng]]
  console.log('drawRoute called with points:', points);
  console.log('_map exists:', !!_map);
  console.log('L exists:', typeof L !== 'undefined');
  
  if(!_map || !Array.isArray(points) || points.length < 2) {
    console.warn('drawRoute: Invalid map or points');
    return;
  }
  
  if (typeof L === 'undefined') {
    console.error('Leaflet (L) is not loaded');
    return;
  }
  
  clearRoute();
  console.log('Creating polyline with points:', points);
  
  _routeLayer = L.polyline(points, { 
    color:'#FF0000',  // Bright red for visibility
    weight:8,         // Thicker line
    opacity:1.0,     // Full opacity
    dashArray:'10 5'  // More visible dashes
  }).addTo(_map);
  
  const [a,b] = points;
  _markers.push(L.circleMarker(a,{ 
    radius:12, 
    color:'#00FF00',  // Bright green
    weight:4, 
    fillOpacity:1.0,
    fill: true
  }).addTo(_map));
  
  _markers.push(L.circleMarker(b,{ 
    radius:12, 
    color:'#0000FF',  // Bright blue
    weight:4, 
    fillOpacity:1.0,
    fill: true
  }).addTo(_map));
  
  const bounds = L.latLngBounds(points);
  _map.fitBounds(bounds, { padding:[28,28], maxZoom:17 });
  
  // Force a redraw to ensure visibility
  setTimeout(() => {
    _map.invalidateSize();
    console.log('Map invalidated for route visibility');
  }, 100);
  
  console.log('Route drawn successfully');
}

export function getMap(){ return _map; }