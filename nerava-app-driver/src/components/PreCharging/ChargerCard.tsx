// Charger card component for pre-charging screen
import type { DiscoveryCharger } from '../../api/chargers'
import type { MerchantSummary } from '../../types'
import { Badge } from '../shared/Badge'
import { NearbyExperiences } from './NearbyExperiences'
import { Button } from '../shared/Button'
import { resolvePhotoUrl } from '../../services/api'
import { track, AnalyticsEvents } from '../../lib/analytics'

interface ChargerCardProps {
  charger: DiscoveryCharger
  onClick?: () => void
  expanded?: boolean
}

export function ChargerCard({ charger, onClick, expanded = false }: ChargerCardProps) {
  // Map nearby_merchants to MerchantSummary format for NearbyExperiences
  const merchantExperiences: MerchantSummary[] = charger.nearby_merchants.map((merchant) => {
    const resolvedPhotoUrl = resolvePhotoUrl(merchant.photo_url)
    
    // Log for Asadas Grill debugging (dev only)
    if (import.meta.env.DEV && merchant.name.toLowerCase().includes('asadas')) {
      console.log(`[ChargerCard] Asadas Grill photo:`, {
        original: merchant.photo_url,
        resolved: resolvedPhotoUrl,
        chargerId: charger.id
      })
    }
    
    return {
      place_id: merchant.place_id,
      name: merchant.name,
      lat: 0, // Not needed for display
      lng: 0, // Not needed for display
      distance_m: merchant.distance_m,
      types: [], // Not provided in API response
      photo_url: resolvedPhotoUrl || undefined,
      badges: merchant.has_exclusive ? ['⚡ Exclusive'] : undefined
    }
  })

  return (
    <div
      data-testid="charger-card"
      className={`relative rounded-2xl overflow-hidden bg-[#F7F8FA] border border-[#E4E6EB] cursor-pointer active:scale-[0.98] transition-transform ${
        expanded ? 'h-full flex flex-col' : ''
      }`}
      style={{
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.1)',
      }}
      onClick={() => {
        track(AnalyticsEvents.CHARGER_VIEWED, { charger_id: charger.id })
        onClick?.()
      }}
    >
      {/* Hero photo - matches FeaturedMerchantCard styling */}
      <div
        className={`relative w-full bg-gray-200 ${
          expanded ? 'flex-1 min-h-[200px]' : 'h-[180px]'
        }`}
      >
        {charger.photo_url ? (
          <>
            <img
              src={resolvePhotoUrl(charger.photo_url) || ''}
              alt={charger.name}
              className="w-full h-full object-cover"
              onError={(e) => {
                // Replace with placeholder on error
                const target = e.target as HTMLImageElement
                target.style.display = 'none'
                const placeholder = target.parentElement?.querySelector('.charger-photo-placeholder') as HTMLElement
                if (placeholder) {
                  placeholder.style.display = 'flex'
                }
              }}
            />
            <div className="charger-photo-placeholder hidden w-full h-full bg-gradient-to-br from-[#1a1a2e] to-[#16213e] flex flex-col items-center justify-center text-white absolute inset-0">
              <svg className="w-16 h-16 mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span className="text-sm opacity-70">{charger.network}</span>
            </div>
          </>
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

      {/* Header section - Compact */}
      <div className="px-4 pt-3 pb-3">
        <h3 className="text-lg font-semibold text-[#050505] truncate" title={charger.name}>
          {charger.name}
        </h3>
        {charger.network && (
          <p className="text-xs text-[#656A6B]">{charger.network}</p>
        )}

        {/* Charger details - inline */}
        <div className="flex items-center gap-3 mt-1 text-xs text-[#656A6B]">
          <div className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <span>{charger.stalls} stalls</span>
          </div>
          <div className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>{charger.kw}kW</span>
          </div>
        </div>

        {/* Nearby experiences */}
        {merchantExperiences.length > 0 && (
          <NearbyExperiences experiences={merchantExperiences} chargerId={charger.id} />
        )}
      </div>
    </div>
  )
}

