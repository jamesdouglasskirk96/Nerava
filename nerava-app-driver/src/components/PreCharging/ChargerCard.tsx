// Charger card component for pre-charging screen
import type { DiscoveryCharger } from '../../api/chargers'
import type { MerchantSummary } from '../../types'
import { Badge } from '../shared/Badge'
import { NearbyExperiences } from './NearbyExperiences'
import { Button } from '../shared/Button'
import { resolvePhotoUrl } from '../../services/api'

interface ChargerCardProps {
  charger: DiscoveryCharger
  onClick?: () => void
  expanded?: boolean
}

export function ChargerCard({ charger, onClick, expanded = false }: ChargerCardProps) {
  // Map nearby_merchants to MerchantSummary format for NearbyExperiences
  const merchantExperiences: MerchantSummary[] = charger.nearby_merchants.map((merchant) => ({
    place_id: merchant.place_id,
    name: merchant.name,
    lat: 0, // Not needed for display
    lng: 0, // Not needed for display
    distance_m: merchant.distance_m,
    types: [], // Not provided in API response
    photo_url: resolvePhotoUrl(merchant.photo_url) || undefined,
    badges: merchant.has_exclusive ? ['⚡ Exclusive'] : undefined
  }))

  return (
    <div
      data-testid="charger-card"
      className={`relative rounded-2xl overflow-hidden bg-[#F7F8FA] border border-[#E4E6EB] cursor-pointer active:scale-[0.98] transition-transform ${
        expanded ? 'h-full flex flex-col' : ''
      }`}
      style={{
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.1)',
      }}
      onClick={onClick}
    >
      {/* Hero photo - matches FeaturedMerchantCard styling */}
      <div
        className={`relative w-full bg-gray-200 ${
          expanded ? 'flex-1 min-h-[200px]' : 'h-[180px]'
        }`}
      >
        {charger.photo_url ? (
          <img
            src={resolvePhotoUrl(charger.photo_url) || ''}
            alt={charger.name}
            className="w-full h-full object-cover"
          />
        ) : (
          // Placeholder for chargers without photos
          <div className="w-full h-full bg-gradient-to-br from-[#1a1a2e] to-[#16213e] flex flex-col items-center justify-center text-white">
            <svg className="w-16 h-16 mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="text-sm opacity-70">{charger.network}</span>
          </div>
        )}

        {/* Gradient overlay */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'linear-gradient(to top, rgba(0, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0) 50%)',
          }}
        />

        {/* Drive time badge - bottom left overlay */}
        <div className="absolute bottom-[18px] left-5">
          <Badge variant="walk-time">{charger.drive_time_min} min drive</Badge>
        </div>
      </div>

      {/* Header section - More compact */}
      <div className="px-5 pt-5 pb-5 space-y-1">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="text-[24px] font-medium leading-8 text-[#050505] mb-1" style={{ letterSpacing: '0.07px' }}>{charger.name}</h3>
            {charger.network && (
              <p className="text-xs text-[#656A6B]">{charger.network}</p>
            )}
          </div>
        </div>

        {/* Charger details */}
        <div className="flex items-center gap-4 text-xs text-[#656A6B]">
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
            <span>{charger.stalls} stalls</span>
          </div>
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <span>{charger.kw}kW</span>
          </div>
        </div>

        {/* Address */}
        {charger.address && (
          <p className="text-sm font-normal leading-5 text-[#656A6B] mt-1" style={{ letterSpacing: '-0.15px' }}>{charger.address}</p>
        )}

        {/* Nearby experiences */}
        {merchantExperiences.length > 0 && (
          <div className="mt-2">
            <NearbyExperiences experiences={merchantExperiences} chargerId={charger.id} />
          </div>
        )}

        {/* Action hint */}
        <p className="text-sm text-[#1877F2] mt-2">
          Tap to see nearby experiences →
        </p>
      </div>
    </div>
  )
}

