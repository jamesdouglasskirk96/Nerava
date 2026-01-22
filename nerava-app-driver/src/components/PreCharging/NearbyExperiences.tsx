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
    <div className="mt-4 pt-4 border-t border-gray-200">
      <p className="text-sm font-semibold text-gray-800 mb-3">Nearby experiences</p>

      {/* Horizontal scroll container */}
      <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
        {validExperiences.map((exp) => {
          const category = exp.types?.[0] ? normalizeCategory(exp.types[0]) : 'Other'
          const walkTime = Math.round(exp.distance_m / 80)
          const hasExclusive = exp.badges?.some(b => b.includes('Exclusive'))
          const photoUrl = resolvePhotoUrl(exp.photo_url)

          return (
            <div
              key={exp.place_id}
              onClick={() => handleMerchantClick(exp.place_id)}
              className="flex-shrink-0 w-[160px] rounded-xl overflow-hidden bg-white border border-gray-200 shadow-sm cursor-pointer active:scale-[0.98] transition-transform"
            >
              {/* Photo */}
              <div className="relative h-[100px] bg-gray-100">
                {photoUrl ? (
                  <img
                    src={photoUrl}
                    alt={exp.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <PhotoPlaceholder category={category} merchantName={exp.name} className="h-full" />
                )}

                {/* Walk time badge */}
                <div className="absolute bottom-2 left-2">
                  <Badge variant="walk-time" className="text-[10px] px-2 py-1">
                    {walkTime} min
                  </Badge>
                </div>
              </div>

              {/* Info */}
              <div className="p-2.5">
                <div className="flex items-start justify-between gap-1">
                  <h4 className="text-sm font-medium text-gray-900 truncate flex-1">
                    {exp.name}
                  </h4>
                  {hasExclusive && (
                    <span className="text-xs">⭐</span>
                  )}
                </div>
                <p className="text-xs text-gray-500 truncate mt-0.5">
                  {exp.types?.slice(0, 2).map(t => normalizeCategory(t)).join(' · ') || category}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

