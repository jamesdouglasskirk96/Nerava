import { useNavigate } from 'react-router-dom'
import type { MerchantSummary } from '../../types'
import { Badge } from '../shared/Badge'
import { PhotoPlaceholder, normalizeCategory } from '../../ui/categoryLogos'

interface ExtendedMerchant extends MerchantSummary {
  brought_to_you_by?: string
  category_display?: string
}

interface FeaturedMerchantCardProps {
  merchant: ExtendedMerchant
  onClick?: () => void
}

export function FeaturedMerchantCard({ merchant, onClick }: FeaturedMerchantCardProps) {
  const navigate = useNavigate()
  const walkTime = merchant.walk_time_s 
    ? Math.round(merchant.walk_time_s / 60) 
    : Math.round((merchant.distance_m || 0) / 80) // Approximate walk time in minutes (80m/min)
  const category = merchant.types?.[0] ? normalizeCategory(merchant.types[0]) : 'Other'
  const hasSponsored = merchant.badges?.includes('Sponsored')
  const hasExclusive = merchant.is_primary || merchant.badges?.includes('Exclusive')
  const categoryDisplay = merchant.category_display || merchant.types?.slice(0, 2).join(' • ') || category
  const broughtToYouBy = merchant.brought_to_you_by
  
  // Use photo_urls[0] if available, fallback to photo_url
  const photoUrl = (merchant as any).photo_urls?.[0] || merchant.photo_url

  const handleClick = () => {
    if (onClick) {
      onClick()
    } else {
      // Default: navigate to merchant details
      const merchantId = merchant.place_id || merchant.id || ''
      navigate(`/merchant/${merchantId}?charger_id=canyon_ridge_tesla`)
    }
  }

  return (
    <div
      data-testid="featured-merchant"
      className="relative rounded-2xl overflow-hidden bg-[#F7F8FA] border border-[#E4E6EB] cursor-pointer active:scale-[0.98] transition-transform"
      style={{
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.1)',
      }}
      onClick={handleClick}
    >
      {/* Photo - Reduced height for mobile viewport (was 256px, now 180px) */}
      <div className="relative w-full h-[180px] bg-gray-200">
        {photoUrl ? (
          <img
            src={photoUrl}
            alt={merchant.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              // Fallback to placeholder on error
              const target = e.target as HTMLImageElement
              target.style.display = 'none'
              const placeholder = target.nextElementSibling as HTMLElement
              if (placeholder) placeholder.style.display = 'flex'
            }}
          />
        ) : null}
        {!photoUrl && (
          <PhotoPlaceholder category={category} merchantName={merchant.name} />
        )}
        
        {/* Gradient overlay - black 40% opacity at bottom, transparent at top */}
        <div 
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'linear-gradient(to top, rgba(0, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0) 50%, rgba(0, 0, 0, 0) 100%)',
          }}
        />
        
        {/* "X min walk" badge - Bottom-left overlay - Matching Figma positioning: 18px from bottom, 20px from left */}
        <div className="absolute bottom-[18px] left-5">
          <Badge variant="walk-time">{walkTime} min walk</Badge>
        </div>
        
        {/* Open/Closed badge - Top-left overlay */}
        {merchant.open_now !== undefined && (
          <div className="absolute top-4 left-5">
            <Badge variant={merchant.open_now ? "success" : "error"}>
              {merchant.open_now ? 'Open' : 'Closed'}
            </Badge>
          </div>
        )}
        
        {/* "⚡ Sponsored" badge - Top-right overlay - Matching Figma positioning: 16px from top, 13px from right */}
        {hasSponsored && (
          <div className="absolute top-4 right-[13px]">
            <Badge variant="sponsored">⚡ Sponsored</Badge>
          </div>
        )}
      </div>

      {/* Merchant info - Exact padding from Figma: 20px horizontal, 20px top */}
      <div className="px-5 pt-5 pb-5 space-y-1">
        {/* Title row with Exclusive badge */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            {/* Title: 24px Medium, line-height 32px, letter-spacing 0.07px */}
            <h3 
              className="text-[24px] font-medium leading-8 text-[#050505]"
              style={{ letterSpacing: '0.07px' }}
            >
              {merchant.name}
            </h3>
            
            {/* Subtitle: "Brought to you by..." - 12px Regular, line-height 16px */}
            {broughtToYouBy && (
              <p className="text-xs font-normal leading-4 text-[#656A6B] mt-1">
                {broughtToYouBy}
              </p>
            )}
            
            {/* Exclusive description */}
            {merchant.exclusive_description && (
              <p className="text-xs font-normal leading-4 text-[#656A6B] mt-1">
                {merchant.exclusive_description}
              </p>
            )}
            
            {/* Open until */}
            {merchant.open_until && (
              <p className="text-xs font-normal leading-4 text-[#656A6B] mt-1">
                {merchant.open_until}
              </p>
            )}
          </div>
          
          {/* "⭐ Exclusive" badge - Top-right in content area */}
          {hasExclusive && (
            <div className="ml-2 flex-shrink-0">
              <Badge variant="exclusive">⭐ Exclusive</Badge>
            </div>
          )}
        </div>
        
        {/* Category and rating: 14px Regular, line-height 20px, letter-spacing -0.15px */}
        <div className="flex items-center justify-between">
          <p 
            className="text-sm font-normal leading-5 text-[#656A6B]"
            style={{ letterSpacing: '-0.15px' }}
          >
            {categoryDisplay}
          </p>
          {merchant.rating && (
            <div className="flex items-center gap-1">
              <span className="text-yellow-400 text-sm">★</span>
              <span className="text-sm text-[#656A6B]">{merchant.rating.toFixed(1)}</span>
              {merchant.user_rating_count && (
                <span className="text-xs text-[#656A6B]">({merchant.user_rating_count})</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

