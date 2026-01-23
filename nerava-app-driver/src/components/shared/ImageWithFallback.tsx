// Image component with category icon fallback
import { useState } from 'react'
import { CategoryIcon } from './CategoryIcon'
import { resolvePhotoUrl } from '../../services/api'

interface ImageWithFallbackProps {
  src?: string | null
  alt: string
  category: string
  className?: string
  fallbackClassName?: string
}

/**
 * Image component that shows category icon if imageUrl is null/undefined or fails to load
 * Used in merchant cards throughout the app
 */
export function ImageWithFallback({
  src,
  alt,
  category,
  className = '',
  fallbackClassName = '',
}: ImageWithFallbackProps) {
  const [hasError, setHasError] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Resolve the photo URL (prepend API base URL if relative)
  const resolvedSrc = resolvePhotoUrl(src)

  // If no src or error occurred, show fallback icon
  if (!resolvedSrc || hasError) {
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
        src={resolvedSrc}
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

