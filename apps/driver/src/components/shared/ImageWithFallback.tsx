// Image component with category icon fallback
// Fallback chain: brand_image_url > Google Places photo > category icon
import { useState } from 'react'
import { CategoryIcon } from './CategoryIcon'

interface ImageWithFallbackProps {
  src?: string | null
  brandImageUrl?: string | null  // Merchant-uploaded brand image override
  googlePlacesPhoto?: string | null  // Google Places photo
  alt: string
  category: string
  className?: string
  fallbackClassName?: string
}

/**
 * Image component with fallback chain:
 * 1. brand_image_url (merchant override)
 * 2. Google Places photo (src)
 * 3. Category icon (deterministic fallback)
 * Used in merchant cards throughout the app
 */
export function ImageWithFallback({
  src,
  brandImageUrl,
  googlePlacesPhoto,
  alt,
  category,
  className = '',
  fallbackClassName = '',
}: ImageWithFallbackProps) {
  const [hasError, setHasError] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Determine image source priority: brand_image_url > src (Google Places) > null
  const imageSrc = brandImageUrl || src || googlePlacesPhoto || null

  // If no src or error occurred, show fallback icon
  if (!imageSrc || hasError) {
    return (
      <div className={`flex items-center justify-center bg-[#F7F8FA] ${fallbackClassName || className}`}>
        <CategoryIcon 
          category={category} 
          className="text-[#65676B]" 
          size={48}
        />
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      <img
        src={imageSrc}
        alt={alt}
        className={`w-full h-full object-cover ${className}`}
        onError={() => {
          setHasError(true)
          setIsLoading(false)
        }}
        onLoad={() => setIsLoading(false)}
      />
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#F7F8FA]">
          <CategoryIcon 
            category={category} 
            className="text-[#65676B] animate-pulse" 
            size={48}
          />
        </div>
      )}
    </div>
  )
}

