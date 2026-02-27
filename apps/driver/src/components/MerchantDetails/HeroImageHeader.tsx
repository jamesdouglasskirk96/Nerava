import { X, Heart, Share2 } from 'lucide-react'
import { PhotoPlaceholder, normalizeCategory } from '../../ui/categoryLogos'
import { Badge } from '../shared/Badge'
import { FEATURE_FLAGS } from '../../config/featureFlags'

interface HeroImageHeaderProps {
  photoUrls?: string[]
  photoUrl?: string  // Keep for backward compatibility
  merchantName: string
  category?: string
  walkTime?: string  // e.g., "3 min walk" or "60 minutes remaining"
  isExclusive?: boolean
  isExclusiveActive?: boolean  // When active, show "Exclusive Active" badge
  isFavorited?: boolean
  onClose?: () => void
  onFavorite?: () => void
  onShare?: () => void
}

export function HeroImageHeader({
  photoUrls,
  photoUrl,
  merchantName,
  category,
  walkTime,
  isExclusive = false,
  isExclusiveActive = false,
  isFavorited = false,
  onClose,
  onFavorite,
  onShare
}: HeroImageHeaderProps) {
  const normalizedCategory = category ? normalizeCategory(category) : 'Other'
  
  // Use photo_urls[0] if available, fallback to photo_url, then placeholder
  const imageUrl = photoUrls?.[0] || photoUrl

  return (
    <div className="relative w-full h-64 bg-gray-200">
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={merchantName}
          className="w-full h-full object-cover"
        />
      ) : (
        <PhotoPlaceholder category={normalizedCategory} merchantName={merchantName} className="h-64" />
      )}
      
      {/* X Close button - top-left */}
      <button
        onClick={onClose}
        className="absolute top-4 left-4 w-11 h-11 rounded-full bg-white/95 backdrop-blur-sm flex items-center justify-center shadow-md hover:bg-white active:scale-95 transition-all z-10"
        aria-label="Close"
      >
        <X className="w-6 h-6 text-gray-900" />
      </button>

      {/* Heart and Share buttons - top-right */}
      <div className="absolute top-4 right-4 flex items-center gap-2 z-10">
        <button
          onClick={onFavorite}
          className={`w-11 h-11 rounded-full backdrop-blur-sm flex items-center justify-center shadow-md hover:bg-white active:scale-95 transition-all ${
            isFavorited ? 'bg-[#1877F2] text-white' : 'bg-white/95 text-gray-900'
          }`}
          aria-label={isFavorited ? 'Remove from favorites' : 'Add to favorites'}
        >
          <Heart className={`w-5 h-5 ${isFavorited ? 'fill-current' : ''}`} aria-hidden="true" />
        </button>
        <button
          onClick={onShare}
          className="w-11 h-11 rounded-full bg-white/95 backdrop-blur-sm flex items-center justify-center shadow-md hover:bg-white active:scale-95 transition-all"
          aria-label="Share merchant"
        >
          <Share2 className="w-5 h-5 text-gray-900" aria-hidden="true" />
        </button>
      </div>

      {/* Exclusive Active badge - top-left (replaces close button position when active) */}
      {isExclusiveActive && (
        <div className="absolute top-4 left-16 z-10">
          <span className="inline-flex items-center px-3 py-1.5 rounded-full bg-blue-600 text-white text-sm font-medium">
            {FEATURE_FLAGS.LIVE_COORDINATION_UI_V1 ? 'Active Session' : 'Exclusive Active'}
          </span>
        </div>
      )}

      {/* Walk time badge - bottom-left */}
      {walkTime && (
        <div className="absolute bottom-4 left-4 z-10">
          <Badge variant={isExclusiveActive ? "default" : "walk-time"}>{walkTime}</Badge>
        </div>
      )}

      {/* Exclusive badge - bottom-right (only when NOT active) */}
      {isExclusive && !isExclusiveActive && (
        <div className="absolute bottom-4 right-4 z-10 flex items-center gap-2">
          <Badge variant="exclusive">Exclusive</Badge>
        </div>
      )}
    </div>
  )
}

