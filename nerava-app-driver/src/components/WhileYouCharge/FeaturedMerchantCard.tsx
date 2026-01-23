import { useState } from 'react'
import type { MerchantSummary } from '../../types'
import { Badge } from '../shared/Badge'
import { PhotoPlaceholder, normalizeCategory } from '../../ui/categoryLogos'
import { resolvePhotoUrl } from '../../services/api'
import { track, AnalyticsEvents } from '../../lib/analytics'

interface ExtendedMerchant extends MerchantSummary {
  brought_to_you_by?: string
  category_display?: string
}

interface FeaturedMerchantCardProps {
  merchant: ExtendedMerchant
  onClick?: () => void
  expanded?: boolean
}

export function FeaturedMerchantCard({
  merchant,
  onClick,
  expanded = false,
}: FeaturedMerchantCardProps) {
  const walkTime = Math.round(merchant.distance_m / 80) // Approximate walk time in minutes (80m/min)
  const category = merchant.types?.[0] ? normalizeCategory(merchant.types[0]) : 'Other'
  const hasSponsored = merchant.badges?.includes('Sponsored')
  const hasExclusive = merchant.badges?.includes('Exclusive')
  const categoryDisplay = merchant.category_display || merchant.types?.slice(0, 2).join(' • ') || category
  const broughtToYouBy = merchant.brought_to_you_by
  const [imageError, setImageError] = useState(false)
  const photoUrl = resolvePhotoUrl(merchant.photo_url)
  
  // Log for Asadas Grill debugging (dev only)
  if (import.meta.env.DEV && merchant.name.toLowerCase().includes('asadas')) {
    console.log(`[FeaturedMerchantCard] Asadas Grill photo:`, {
      original: merchant.photo_url,
      resolved: photoUrl,
      place_id: merchant.place_id
    })
  }

  return (
    <div
      data-testid="featured-merchant"
      className={`relative rounded-2xl overflow-hidden bg-[#F7F8FA] border border-[#E4E6EB] cursor-pointer active:scale-[0.98] transition-transform ${
        expanded ? 'h-full flex flex-col' : ''
      }`}
      style={{
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.1)',
      }}
      onClick={() => {
        track(AnalyticsEvents.MERCHANT_CARD_VIEWED, { merchant_id: merchant.place_id })
        onClick?.()
      }}
    >
      {/* Photo - Reduced height for mobile viewport (was 256px, now 180px) */}
      <div
        className={`relative w-full bg-gray-200 ${
          expanded ? 'flex-1 min-h-[200px]' : 'h-[180px]'
        }`}
      >
        {photoUrl && !imageError ? (
          <img
            src={photoUrl}
            alt={merchant.name}
            className="w-full h-full object-cover"
            onError={() => {
              console.error(`Failed to load photo for ${merchant.name}:`, photoUrl)
              setImageError(true)
            }}
            onLoad={() => {
              if (import.meta.env.DEV && merchant.name.toLowerCase().includes('asadas')) {
                console.log(`[FeaturedMerchantCard] Asadas Grill photo loaded successfully:`, photoUrl)
              }
            }}
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-[#1a1a2e] to-[#16213e] flex flex-col items-center justify-center text-white">
            <PhotoPlaceholder category={category} merchantName={merchant.name} />
          </div>
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
        
        {/* Hide Sponsored for MVP - reintroduce once users understand Exclusive
        {hasSponsored && (
          <div className="absolute top-4 right-[13px]">
            <Badge variant="sponsored">⚡ Sponsored</Badge>
          </div>
        )}
        */}
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
          </div>
          
          {/* "⭐ Exclusive" badge - Top-right in content area */}
          {hasExclusive && (
            <div className="ml-2 flex-shrink-0 text-right">
              <Badge variant="exclusive">⭐ Exclusive</Badge>
              <p className="text-[10px] text-[#656A6B] mt-1 py-0.5 leading-tight">Free perk while charging</p>
            </div>
          )}
        </div>
        
        {/* Category: 14px Regular, line-height 20px, letter-spacing -0.15px */}
        <p 
          className="text-sm font-normal leading-5 text-[#656A6B]"
          style={{ letterSpacing: '-0.15px' }}
        >
          {categoryDisplay}
        </p>
        
        {/* Action hint */}
        <p className="text-sm text-[#1877F2] mt-2">
          Tap to see your free perk →
        </p>
      </div>
    </div>
  )
}

