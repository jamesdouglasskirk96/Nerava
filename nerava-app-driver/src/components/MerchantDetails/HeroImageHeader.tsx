import { useState } from 'react'
import { PhotoPlaceholder, normalizeCategory } from '../../ui/categoryLogos'
import { Badge } from '../shared/Badge'
import { resolvePhotoUrl } from '../../services/api'

interface HeroImageHeaderProps {
  photoUrls?: string[]
  photoUrl?: string  // Keep for backward compatibility
  merchantName: string
  category?: string
  walkTime?: string  // e.g., "3 min walk"
  isExclusive?: boolean
  isFavorite?: boolean
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
  isFavorite = false,
  onClose,
  onFavorite,
  onShare
}: HeroImageHeaderProps) {
  const normalizedCategory = category ? normalizeCategory(category) : 'Other'
  
  // Use photo_urls[0] if available, fallback to photo_url, then placeholder
  // Resolve relative URLs to use API base URL
  const imageUrl = resolvePhotoUrl(photoUrls?.[0] || photoUrl)

  // Use smaller height when there's no photo
  const hasImage = !!imageUrl

  const [imageError, setImageError] = useState(false)
  const [imageLoading, setImageLoading] = useState(true)

  return (
    <div className={`relative w-full bg-gray-200 ${hasImage && !imageError ? 'h-[28vh] max-h-[220px]' : 'h-[120px]'}`}>
      {imageUrl && !imageError ? (
        <>
          <img
            src={imageUrl}
            alt={merchantName}
            className="w-full h-full object-cover"
            onError={(e) => {
              console.error(`Failed to load image for ${merchantName}:`, imageUrl)
              setImageError(true)
              setImageLoading(false)
            }}
            onLoad={() => {
              setImageLoading(false)
            }}
          />
          {imageLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-200">
              <PhotoPlaceholder category={normalizedCategory} merchantName={merchantName} className="h-full" />
            </div>
          )}
        </>
      ) : (
        <PhotoPlaceholder category={normalizedCategory} merchantName={merchantName} className="h-full" />
      )}

      {/* Walk time badge - bottom-left */}
      {walkTime && (
        <div className="absolute bottom-4 left-4 z-10">
          <Badge variant="walk-time">{walkTime}</Badge>
        </div>
      )}

      {/* Exclusive badge - bottom-right */}
      {isExclusive && (
        <div className="absolute bottom-4 right-4 z-10">
          <Badge variant="exclusive">Exclusive</Badge>
        </div>
      )}
    </div>
  )
}

