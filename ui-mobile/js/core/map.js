/* globals L */
let _map, _routeLayer, _markers = [];
const MAP_ID = 'map';

// Import branded pin functions (will be loaded dynamically)
let createChargerPinIcon, updatePinScale, animatePinTap;

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
  
  // If points are too close, add intermediate points to make route visible
  let routePoints = [...points];
  const [start, end] = points;
  const distance = start.distanceTo ? start.distanceTo(end) : L.latLng(start).distanceTo(L.latLng(end));
  
  if (distance < 100) { // Less than 100 meters
    console.log('Points too close, adding intermediate points');
    const midLat = (start[0] + end[0]) / 2;
    const midLng = (start[1] + end[1]) / 2;
    const offset = 0.001; // Small offset to make route visible
    routePoints = [
      start,
      [midLat + offset, midLng + offset],
      [midLat - offset, midLng - offset],
      end
    ];
    console.log('New route points:', routePoints);
  }
  
  _routeLayer = L.polyline(routePoints, { 
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
  
  // Ensure we have proper bounds and zoom
  const bounds = L.latLngBounds(routePoints);
  console.log('Bounds:', bounds);
  console.log('Points distance:', bounds.getNorthEast().distanceTo(bounds.getSouthWest()));
  
  // If points are too close, expand the bounds
  if (bounds.getNorthEast().distanceTo(bounds.getSouthWest()) < 100) {
    console.log('Points too close, expanding bounds');
    bounds.extend(bounds.getCenter().toBounds(1000)); // 1km buffer
  }
  
  _map.fitBounds(bounds, { padding:[50,50], maxZoom:16 });
  
  // Force a redraw to ensure visibility
  setTimeout(() => {
    _map.invalidateSize();
    console.log('Map invalidated for route visibility');
  }, 200);
  
  console.log('Route drawn successfully');
}

export function getMap(){ return _map; }

// Persistent layer for charger pins
let _stationLayer = null;

export function getOrCreateStationLayer() {
  if (!_map) return null;
  if (!_stationLayer) {
    _stationLayer = L.layerGroup().addTo(_map);
  }
  return _stationLayer;
}

export function clearStations() {
  if (_stationLayer) {
    _stationLayer.clearLayers();
  }
}

// Lazy load charger pin functions
async function loadChargerPinFunctions() {
  if (!createChargerPinIcon) {
    const module = await import('./chargerPins.js');
    createChargerPinIcon = module.createChargerPinIcon;
    updatePinScale = module.updatePinScale;
    animatePinTap = module.animatePinTap;
  }
}

export async function addStationDot(station, { onClick } = {}) {
  const layer = getOrCreateStationLayer();
  if (!layer) return null;
  
  // Load charger pin functions if not already loaded
  await loadChargerPinFunctions();
  
  // Get network and status from station
  const network = station.network || station.network_name || 'generic';
  const status = station.status || 'available'; // available, in_use, broken, unknown
  
  // Get current zoom level
  const zoom = _map ? _map.getZoom() : 15;
  
  // Create branded charger pin icon
  const icon = createChargerPinIcon(network, status, zoom);
  
  // Create marker with branded pin
  const m = L.marker([station.lat, station.lng], { icon });
  
  // Handle click with animation
  if (onClick) {
    m.on('click', () => {
      animatePinTap(m);
      onClick(station);
    });
  }
  
  // Update scale on zoom change (only attach once per map)
  if (_map && !_map._pinZoomHandlerAttached) {
    _map.on('zoomend', () => {
      const currentZoom = _map.getZoom();
      // Update all pins in the station layer
      if (_stationLayer) {
        _stationLayer.eachLayer((marker) => {
          if (marker instanceof L.Marker) {
            updatePinScale(marker, currentZoom);
          }
        });
      }
    });
    _map._pinZoomHandlerAttached = true;
  }
  
  m.addTo(layer);
  return m;
}

export function fitToStations(stations, padding = 0.15) {
  if (!_map || !stations?.length) return;
  const bounds = L.latLngBounds(stations.map(s => [s.lat, s.lng]));
  _map.fitBounds(bounds.pad(padding), { animate: true });
}