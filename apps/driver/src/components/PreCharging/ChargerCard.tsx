// Charger card component for pre-charging screen
import type { ChargerWithExperiences } from '../../mock/types'
import { Badge } from '../shared/Badge'
import { LiveStallIndicator } from '../shared/LiveStallIndicator'
import { NearbyExperiences } from './NearbyExperiences'
import { Button } from '../shared/Button'

interface ChargerCardProps {
  charger: ChargerWithExperiences
  onClick?: () => void
}

export function ChargerCard({ charger, onClick }: ChargerCardProps) {
  const driveTime = Math.round(charger.distance_m / 1000) // Approximate drive time (rough estimate)

  return (
    <div
      data-testid="charger-card"
      className="relative rounded-xl overflow-hidden bg-white shadow-lg cursor-pointer active:scale-[0.98] transition-transform"
      onClick={onClick}
    >
      {/* Header section - More compact */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 mb-1">{charger.name}</h3>
            {charger.network_name && (
              <p className="text-xs text-gray-600">{charger.network_name}</p>
            )}
          </div>
          <Badge variant="featured">{driveTime} min drive</Badge>
        </div>

        {/* Charger details */}
        <div className="flex flex-col gap-2 mt-2">
          {/* Stall availability indicator */}
          <LiveStallIndicator
            availableStalls={(charger as any).availableStalls ?? charger.stalls}
            totalStalls={charger.stalls}
            lastUpdatedAt={(charger as any).lastUpdatedAt}
          />
          {/* Other charger details */}
          <div className="flex items-center gap-4 text-xs text-gray-600">
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <span>{charger.plug_types.join(', ')}</span>
          </div>
          {charger.rating && (
            <div className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              <span>{charger.rating.toFixed(1)}</span>
            </div>
          )}
          </div>
        </div>

        {/* Nearby experiences */}
        {charger.nearby_experiences && charger.nearby_experiences.length > 0 && (
          <NearbyExperiences experiences={charger.nearby_experiences} />
        )}

        {/* CTA button - Ensure it's visible */}
        <div className="mt-3 flex-shrink-0">
          <Button variant="primary" className="w-full" onClick={(e) => {
            e.stopPropagation()
            // TODO: Wire to backend navigation
            console.log('Navigate to charger:', charger.id)
            onClick?.()
          }}>
            Navigate to Charger
          </Button>
        </div>
      </div>
    </div>
  )
}

