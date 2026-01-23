// Nearby experiences preview (2 tiles) inside charger card, or single primary merchant
import { useNavigate } from 'react-router-dom'
import type { MerchantSummary } from '../../types'
import { PhotoPlaceholder, normalizeCategory } from '../../ui/categoryLogos'
import { Badge } from '../shared/Badge'

interface NearbyExperiencesProps {
  experiences: MerchantSummary[]
  maxItems?: number
  onMerchantClick?: (merchant: MerchantSummary) => void
}

export function NearbyExperiences({ experiences, maxItems = 2, onMerchantClick }: NearbyExperiencesProps) {
  const navigate = useNavigate()
  
  // Filter out null/undefined experiences before slicing
  const validExperiences = experiences.filter((exp) => exp && exp.place_id)
  
  const handleMerchantClick = (merchant: MerchantSummary) => {
    if (onMerchantClick) {
      onMerchantClick(merchant)
    } else {
      // Default: navigate to merchant details
      const merchantId = merchant.place_id || merchant.id || ''
      navigate(`/merchant/${merchantId}`)
    }
  }
  
  // If there's only one experience and it's primary, show single card with exclusive badge
  if (validExperiences.length === 1 && validExperiences[0].is_primary) {
    const exp = validExperiences[0]
    const category = exp.types?.[0] ? normalizeCategory(exp.types[0]) : 'Other'
    
    return (
      <div className="mt-3 pt-3 border-t border-gray-200">
        <p className="text-xs font-semibold text-gray-700 mb-2">Nearby experience</p>
        <div 
          className="relative rounded-lg overflow-hidden bg-gray-100 aspect-[4/3] cursor-pointer active:scale-[0.98] transition-transform"
          onClick={() => handleMerchantClick(exp)}
        >
          {exp.photo_url ? (
            <img
              src={exp.photo_url}
              alt={exp.name || 'Merchant'}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <PhotoPlaceholder
                category={category}
                merchantName={exp.name || 'Merchant'}
                className="h-full"
              />
            </div>
          )}
          {/* Exclusive badge overlay */}
          {exp.is_primary && exp.exclusive_title && (
            <div className="absolute top-2 right-2">
              <Badge variant="exclusive">⭐ Exclusive</Badge>
            </div>
          )}
          {/* Open/Closed badge */}
          {exp.open_now !== undefined && (
            <div className="absolute top-2 left-2">
              <Badge variant={exp.open_now ? "success" : "error"}>
                {exp.open_now ? 'Open' : 'Closed'}
              </Badge>
            </div>
          )}
          {/* Merchant info overlay */}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="text-white font-semibold text-sm mb-1">{exp.name || 'Merchant'}</h4>
                {exp.exclusive_description && (
                  <p className="text-white/90 text-xs">{exp.exclusive_description}</p>
                )}
                {exp.open_until && (
                  <p className="text-white/70 text-xs mt-1">{exp.open_until}</p>
                )}
                {exp.rating && (
                  <div className="flex items-center gap-1 mt-1">
                    <span className="text-yellow-400 text-xs">★</span>
                    <span className="text-white text-xs">{exp.rating.toFixed(1)}</span>
                    {exp.user_rating_count && (
                      <span className="text-white/70 text-xs">({exp.user_rating_count})</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }
  
  // Default: grid layout for multiple experiences
  const displayExperiences = validExperiences.slice(0, maxItems)

  if (displayExperiences.length === 0) {
    return null
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-200">
      <p className="text-xs font-semibold text-gray-700 mb-2">Nearby experiences</p>
      <div className="grid grid-cols-2 gap-2">
        {displayExperiences.map((exp) => {
          const category = exp.types?.[0] ? normalizeCategory(exp.types[0]) : 'Other'
          return (
            <div
              key={exp.place_id}
              className="relative rounded-lg overflow-hidden bg-gray-100 aspect-square cursor-pointer active:scale-[0.98] transition-transform"
              onClick={() => handleMerchantClick(exp)}
            >
              {exp.photo_url ? (
                <img
                  src={exp.photo_url}
                  alt={exp.name || 'Merchant'}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <PhotoPlaceholder
                    category={category}
                    merchantName={exp.name || 'Merchant'}
                    className="h-full"
                  />
                </div>
              )}
              {exp.is_primary && (
                <div className="absolute top-1 right-1">
                  <Badge variant="exclusive" className="text-xs">⭐</Badge>
                </div>
              )}
              <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs px-2 py-1 truncate">
                {exp.name || 'Merchant'}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

