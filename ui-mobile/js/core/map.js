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
  if(!_map || !Array.isArray(points) || points.length < 2) return;
  clearRoute();
  _routeLayer = L.polyline(points, { color:'#3B82F6', weight:6, opacity:0.6, dashArray:'8 10' }).addTo(_map);
  const [a,b] = points;
  _markers.push(L.circleMarker(a,{ radius:7, color:'#2563EB', weight:6, opacity:0.25 }).addTo(_map));
  _markers.push(L.circleMarker(b,{ radius:7, color:'#2563EB', weight:6, opacity:1 }).addTo(_map));
  const bounds = L.latLngBounds(points);
  _map.fitBounds(bounds, { padding:[28,28], maxZoom:17 });
}

export function getMap(){ return _map; }