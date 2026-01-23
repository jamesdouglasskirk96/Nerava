// Nearby experiences preview - horizontal scrollable list
import { useNavigate } from 'react-router-dom'
import type { MerchantSummary } from '../../types'
import { PhotoPlaceholder, normalizeCategory } from '../../ui/categoryLogos'
import { Badge } from '../shared/Badge'
import { resolvePhotoUrl } from '../../services/api'

interface NearbyExperiencesProps {
  experiences: MerchantSummary[]
  chargerId?: string
}

export function NearbyExperiences({ experiences, chargerId }: NearbyExperiencesProps) {
  const navigate = useNavigate()

  const validExperiences = experiences.filter((exp) => exp && exp.place_id)

  if (validExperiences.length === 0) {
    return null
  }

  const handleMerchantClick = (placeId: string) => {
    navigate(`/m/${placeId}${chargerId ? `?charger_id=${chargerId}` : ''}`)
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-200">
      <p className="text-xs font-semibold text-gray-700 mb-2">Nearby experiences</p>

      {/* Horizontal scroll container - more compact */}
      <div className="flex gap-2 overflow-x-auto pb-1 -mx-4 px-4 scrollbar-hide">
        {validExperiences.map((exp) => {
          const category = exp.types?.[0] ? normalizeCategory(exp.types[0]) : 'Other'
          const walkTime = Math.round(exp.distance_m / 80)
          const hasExclusive = exp.badges?.some(b => b.includes('Exclusive'))
          const photoUrl = resolvePhotoUrl(exp.photo_url)
          
          // Log photo URL for debugging (dev only)
          if (import.meta.env.DEV && exp.name.toLowerCase().includes('asadas')) {
            console.log(`[Asadas Grill] Photo URL:`, { photoUrl, original: exp.photo_url, place_id: exp.place_id })
          }

          return (
            <div
              key={exp.place_id}
              onClick={(e) => {
                e.stopPropagation()
                handleMerchantClick(exp.place_id)
              }}
              className="flex-shrink-0 w-[140px] rounded-lg overflow-hidden bg-white border border-gray-200 shadow-sm cursor-pointer active:scale-[0.98] transition-transform"
            >
              {/* Photo - more compact */}
              <div className="relative h-[80px] bg-gray-100">
                {photoUrl ? (
                  <img
                    src={photoUrl}
                    alt={exp.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      console.error(`Failed to load photo for ${exp.name}:`, photoUrl)
                      // Replace with placeholder on error
                      const target = e.target as HTMLImageElement
                      target.style.display = 'none'
                      const placeholder = target.parentElement?.querySelector('.photo-placeholder') as HTMLElement
                      if (placeholder) {
                        placeholder.style.display = 'flex'
                      }
                    }}
                    onLoad={() => {
                      if (import.meta.env.DEV && exp.name.toLowerCase().includes('asadas')) {
                        console.log(`[Asadas Grill] Photo loaded successfully:`, photoUrl)
                      }
                    }}
                  />
                ) : null}
                <div className={`photo-placeholder ${photoUrl ? 'hidden' : 'flex'} items-center justify-center h-full`}>
                  <PhotoPlaceholder category={category} merchantName={exp.name} className="h-full" />
                </div>

                {/* Walk time badge */}
                <div className="absolute bottom-1.5 left-1.5">
                  <span className="text-[10px] font-medium text-white bg-[#1877F2] px-1.5 py-0.5 rounded-full">
                    {walkTime} min
                  </span>
                </div>
              </div>

              {/* Info - compact */}
              <div className="p-2">
                <div className="flex items-center justify-between gap-1">
                  <h4 className="text-xs font-medium text-gray-900 truncate flex-1">
                    {exp.name}
                  </h4>
                  {hasExclusive && (
                    <span className="text-[10px]">⚡</span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

