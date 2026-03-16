import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const startIcon = new L.DivIcon({
  className: 'trail-start-marker',
  html: `<div style="
    width:14px;height:14px;border-radius:50%;
    background:#22c55e;border:2.5px solid white;
    box-shadow:0 1px 4px rgba(0,0,0,0.3);
  "></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
})

const endIcon = new L.DivIcon({
  className: 'trail-end-marker',
  html: `<div style="
    width:14px;height:14px;border-radius:50%;
    background:#ef4444;border:2.5px solid white;
    box-shadow:0 1px 4px rgba(0,0,0,0.3);
  "></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
})

const chargerIcon = new L.DivIcon({
  className: 'trail-charger-marker',
  html: `<div style="
    width:24px;height:24px;border-radius:50%;
    background:#1877F2;border:2.5px solid white;
    box-shadow:0 1px 4px rgba(0,0,0,0.3);
    display:flex;align-items:center;justify-content:center;
    font-size:12px;
  ">⚡</div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
})

interface FitTrailBoundsProps {
  points: L.LatLngExpression[]
}

function FitTrailBounds({ points }: FitTrailBoundsProps) {
  const map = useMap()
  const fitted = useRef(false)

  useEffect(() => {
    if (fitted.current || points.length === 0) return
    const bounds = L.latLngBounds(points)
    map.fitBounds(bounds, { padding: [30, 30], maxZoom: 16 })
    fitted.current = true
  }, [points, map])

  return null
}

interface SessionTrailMapProps {
  trail: { lat: number; lng: number; ts: string }[]
  chargerLat?: number | null
  chargerLng?: number | null
}

export function SessionTrailMap({ trail, chargerLat, chargerLng }: SessionTrailMapProps) {
  const positions: [number, number][] = trail.map((p) => [p.lat, p.lng])

  const allPoints: L.LatLngExpression[] = [...positions]
  if (chargerLat && chargerLng) {
    allPoints.push([chargerLat, chargerLng])
  }

  const first = positions[0]
  const last = positions[positions.length - 1]

  return (
    <div className="rounded-lg overflow-hidden border border-[#E4E6EB]" style={{ height: 200 }}>
      <MapContainer
        center={first}
        zoom={15}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
        attributionControl={false}
        dragging={true}
        scrollWheelZoom={false}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <FitTrailBounds points={allPoints} />

        {/* Trail polyline */}
        <Polyline
          positions={positions}
          pathOptions={{ color: '#1877F2', weight: 3, opacity: 0.8 }}
        />

        {/* Charger marker */}
        {chargerLat && chargerLng && (
          <Marker position={[chargerLat, chargerLng]} icon={chargerIcon} />
        )}

        {/* Start marker */}
        <Marker position={first} icon={startIcon} />

        {/* End marker */}
        <Marker position={last} icon={endIcon} />
      </MapContainer>
    </div>
  )
}
