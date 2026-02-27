import { useEffect, useMemo, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { ChargerSummary, MerchantSummary } from '../../types'

// Fix default marker icon path issue with bundlers
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const chargerIcon = new L.DivIcon({
  className: 'charger-marker',
  html: `<div style="
    width:32px;height:32px;border-radius:50%;
    background:#1877F2;border:3px solid white;
    box-shadow:0 2px 6px rgba(0,0,0,0.3);
    display:flex;align-items:center;justify-content:center;
    font-size:16px;
  ">⚡</div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  popupAnchor: [0, -18],
})

const merchantIcon = new L.DivIcon({
  className: 'merchant-marker',
  html: `<div style="
    width:22px;height:22px;border-radius:50%;
    background:#9CA3AF;border:2px solid white;
    box-shadow:0 1px 4px rgba(0,0,0,0.2);
  "></div>`,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -13],
})

const userIcon = new L.DivIcon({
  className: 'user-marker',
  html: `<div style="
    width:16px;height:16px;border-radius:50%;
    background:#3B82F6;border:3px solid white;
    box-shadow:0 0 0 3px rgba(59,130,246,0.3);
  "></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
})

interface FitBoundsProps {
  chargers: ChargerSummary[]
  userLat?: number
  userLng?: number
}

function FitBounds({ chargers, userLat, userLng }: FitBoundsProps) {
  const map = useMap()
  const fitted = useRef(false)

  useEffect(() => {
    if (fitted.current) return
    const points: L.LatLngExpression[] = []

    for (const c of chargers) {
      if (c.lat && c.lng) points.push([c.lat, c.lng])
    }
    if (userLat && userLng) points.push([userLat, userLng])

    if (points.length > 0) {
      const bounds = L.latLngBounds(points)
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 })
      fitted.current = true
    }
  }, [chargers, userLat, userLng, map])

  return null
}

interface ChargerMapProps {
  chargers: ChargerSummary[]
  merchants?: MerchantSummary[]
  userLat?: number
  userLng?: number
  onChargerClick?: (chargerId: string) => void
}

export function ChargerMap({
  chargers,
  merchants = [],
  userLat,
  userLng,
  onChargerClick,
}: ChargerMapProps) {
  // Filter chargers/merchants with valid coords
  const validChargers = useMemo(
    () => chargers.filter((c) => c.lat && c.lng && (c.lat !== 0 || c.lng !== 0)),
    [chargers]
  )
  const validMerchants = useMemo(
    () => merchants.filter((m) => m.lat && m.lng),
    [merchants]
  )

  // Default center: user location, first charger, or Austin TX
  const center: [number, number] = useMemo(() => {
    if (userLat && userLng) return [userLat, userLng]
    if (validChargers.length > 0) return [validChargers[0].lat!, validChargers[0].lng!]
    return [30.267, -97.743]
  }, [userLat, userLng, validChargers])

  return (
    <div className="flex-1 relative" style={{ minHeight: 300 }}>
      <MapContainer
        center={center}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <FitBounds chargers={validChargers} userLat={userLat} userLng={userLng} />

        {/* User location */}
        {userLat && userLng && (
          <Marker position={[userLat, userLng]} icon={userIcon}>
            <Popup>You are here</Popup>
          </Marker>
        )}

        {/* Charger markers */}
        {validChargers.map((c) => (
          <Marker
            key={c.id}
            position={[c.lat!, c.lng!]}
            icon={chargerIcon}
            eventHandlers={{
              click: () => onChargerClick?.(c.id),
            }}
          >
            <Popup>
              <div className="text-sm">
                <p className="font-semibold">{c.name}</p>
                {c.network_name && (
                  <p className="text-gray-500">{c.network_name}</p>
                )}
                {c.campaign_reward_cents != null && c.campaign_reward_cents > 0 && (
                  <p className="text-green-600 font-medium">
                    ${(c.campaign_reward_cents / 100).toFixed(2)} reward
                  </p>
                )}
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Merchant markers */}
        {validMerchants.map((m) => (
          <Marker
            key={m.place_id}
            position={[m.lat, m.lng]}
            icon={merchantIcon}
          >
            <Popup>
              <div className="text-sm">
                <p className="font-semibold">{m.name}</p>
                <p className="text-gray-500">{m.types?.[0] || 'Place'}</p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}
