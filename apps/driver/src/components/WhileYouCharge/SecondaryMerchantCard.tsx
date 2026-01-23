import type { MerchantSummary } from '../../types'
import { Badge } from '../shared/Badge'
import { PhotoPlaceholder, normalizeCategory } from '../../ui/categoryLogos'

interface SecondaryMerchantCardProps {
  merchant: MerchantSummary & { category_display?: string }
  onClick?: () => void
}

export function SecondaryMerchantCard({ merchant, onClick }: SecondaryMerchantCardProps) {
  const walkTime = Math.round(merchant.distance_m / 80)
  const isOnWayOut = merchant.distance_m > 500 // More than 500m = "on your way out"
  const category = merchant.types?.[0] ? normalizeCategory(merchant.types[0]) : 'Other'
  const hasExclusive = merchant.badges?.includes('Exclusive')

  return (
    <div
      data-testid="secondary-merchant"
      className="flex flex-col rounded-2xl bg-[#F7F8FA] border border-[#E4E6EB] cursor-pointer active:scale-[0.98] transition-all overflow-hidden"
      onClick={onClick}
    >
      {/* Photo - 196x123px matching Figma */}
      <div className="relative w-full h-[123px] overflow-hidden bg-gray-200">
        {merchant.photo_url ? (
          <img
            src={merchant.photo_url}
            alt={merchant.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <PhotoPlaceholder category={category} merchantName={merchant.name} />
        )}
      </div>

      {/* Info - Exact padding from Figma: 12px */}
      <div className="px-3 pt-3 pb-3 space-y-1.5">
        {/* Title: 16px Medium, line-height 24px, letter-spacing -0.3125px */}
        <div className="flex items-center justify-between gap-2">
          <h4 
            className="text-base font-medium leading-6 text-[#050505] truncate flex-1"
            style={{ letterSpacing: '-0.3125px' }}
          >
            {merchant.name}
          </h4>
          
          {/* Exclusive badge - smaller size */}
          {hasExclusive && (
            <Badge variant="exclusive" className="px-2.25 pt-[11px] pb-[1px] flex-shrink-0">
              ⭐
            </Badge>
          )}
        </div>
        
        {/* Badge row - "X min walk" or "On your way out" */}
        <div className="flex items-center gap-2">
          {isOnWayOut ? (
            <Badge variant="walk-time-secondary">On your way out</Badge>
          ) : (
            <Badge variant="walk-time-secondary">{walkTime} min walk</Badge>
          )}
        </div>
      </div>
    </div>
  )
}

