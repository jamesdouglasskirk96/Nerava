// Merchant Carousel component matching Figma reference
import { ChevronLeft, ChevronRight, Heart } from 'lucide-react'
import { ImageWithFallback } from '../shared/ImageWithFallback'
import type { MockMerchant } from '../../mock/mockMerchants'
import type { MockCharger } from '../../mock/mockChargers'

type CarouselItem = MockMerchant | (MockCharger & { experiences?: Array<{ id: string; name: string; category: string; walkTime: string; imageUrl?: string | null; badge?: string }> })

interface MerchantSet {
  featured: CarouselItem
  nearby: CarouselItem[]
}

interface MerchantCarouselProps {
  merchantSet: MerchantSet
  isCharging: boolean
  onPrevSet: () => void
  onNextSet: () => void
  currentSetIndex: number
  totalSets: number
  onMerchantClick: (item: CarouselItem) => void
  likedMerchants: Set<string>
}

/**
 * Merchant Carousel showing 3 cards (1 featured + 2 secondary)
 * Displays "Sponsored" badge only if merchant.isSponsored === true
 * Uses fallback icons for missing images
 */
export function MerchantCarousel({
  merchantSet,
  isCharging,
  onPrevSet,
  onNextSet,
  currentSetIndex,
  totalSets,
  onMerchantClick,
  likedMerchants,
}: MerchantCarouselProps) {
  const { featured, nearby } = merchantSet

  // Dynamic font size for merchant/charger titles to ensure single line
  const getTitleFontSize = (name: string) => {
    const length = name.length
    if (length <= 20) return 'text-2xl'
    if (length <= 25) return 'text-xl'
    if (length <= 30) return 'text-lg'
    return 'text-base'
  }

  return (
    <div className="relative h-full flex flex-col justify-start pt-3 px-5 overflow-y-auto min-h-0">
      {/* Featured Merchant Card */}
      <div className="mb-3 flex-shrink-0">
        <div
          className="bg-[#F7F8FA] rounded-2xl overflow-hidden shadow-md border border-[#E4E6EB] cursor-pointer"
          onClick={() => onMerchantClick(featured)}
        >
          {/* Image */}
          <div className="relative h-40 sm:h-48 overflow-hidden">
            <ImageWithFallback
              src={featured.imageUrl}
              alt={featured.name}
              category={featured.category || 'coffee'}
              className="w-full h-full"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />

            {/* Top-right badges on image: Exclusive + Heart */}
            <div className="absolute top-3 right-3 flex items-center gap-2">
              {/* Exclusive Badge */}
              {isCharging && (('badges' in featured && featured.badges && featured.badges.includes('Exclusive')) || ('is_primary' in featured && featured.is_primary) || ('isFeatured' in featured && featured.isFeatured)) && (
                <div className="px-3 py-1.5 bg-white/90 backdrop-blur-sm rounded-full border border-yellow-500/40 shadow-sm">
                  <span className="text-xs font-medium text-yellow-700">⭐ Exclusive</span>
                </div>
              )}
              {/* Heart Icon */}
              {likedMerchants.has(featured.id) && (
                <div className="w-8 h-8 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm border border-[#E4E6EB]">
                  <Heart className="w-4 h-4 text-[#1877F2] fill-[#1877F2]" />
                </div>
              )}
            </div>

            {/* Walk Time Badge on Image */}
            <div className="absolute bottom-3 left-3">
              <div className="px-3 py-1.5 bg-[#1877F2] rounded-full">
                <span className="text-xs text-white font-medium">{featured.walkTime}</span>
              </div>
            </div>

            {/* Sponsored Badge on Image - only if isSponsored === true */}
            {isCharging && 'isSponsored' in featured && featured.isSponsored && (
              <div className="absolute bottom-3 right-3">
                <div className="px-3 py-1.5 bg-white/90 backdrop-blur-sm rounded-full border border-[#E4E6EB]">
                  <span className="text-xs text-[#65676B] font-medium">⚡ Sponsored</span>
                </div>
              </div>
            )}
          </div>

          {/* Content */}
          <div className="p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <h3 className={getTitleFontSize(featured.name)}>{featured.name}</h3>
                {isCharging && 'isSponsored' in featured && featured.isSponsored && !(('badges' in featured && featured.badges && featured.badges.includes('Exclusive')) || ('is_primary' in featured && featured.is_primary) || ('isFeatured' in featured && featured.isFeatured)) && (
                  <p className="text-xs text-[#65676B] mt-1">Brought to you by {featured.name}</p>
                )}
                {!isCharging && (
                  <p className="text-xs text-[#65676B] mt-1">Popular charging destination</p>
                )}
              </div>
            </div>
            {/* Two-line description format: offer text (prominent) + category (secondary) */}
            {'exclusiveOffer' in featured && featured.exclusiveOffer ? (
              <div className="mt-1">
                <p className="text-base font-medium text-[#050505]">{featured.exclusiveOffer}</p>
                {featured.category && (
                  <p className="text-sm text-[#65676B] mt-0.5">{featured.category}</p>
                )}
              </div>
            ) : featured.category ? (
              <p className="text-sm text-[#65676B] mt-1">{featured.category}</p>
            ) : null}

            {/* Nerava Rating for chargers */}
            {!isCharging && 'rating' in featured && featured.rating && (
              <div className="flex items-center gap-1.5 mt-2">
                <span className="text-xs text-[#65676B]">Nerava rating:</span>
                <div className="flex items-center gap-0.5">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <span
                      key={index}
                      className={index < featured.rating! ? 'text-yellow-500' : 'text-[#E4E6EB]'}
                    >
                      ★
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Experiences for chargers (pre-charging mode) */}
            {!isCharging && 'experiences' in featured && featured.experiences && featured.experiences.length > 0 && (
              <div className="mt-4 pt-4 border-t border-[#E4E6EB]">
                <p className="text-xs text-[#65676B] mb-2">Nearby experiences:</p>
                <div className="flex gap-2">
                  {featured.experiences.slice(0, 2).map((exp) => (
                    <div key={exp.id} className="flex-1 bg-white rounded-lg p-2 border border-[#E4E6EB]">
                      <div className="relative h-16 rounded overflow-hidden mb-1.5">
                        <ImageWithFallback
                          src={exp.imageUrl}
                          alt={exp.name}
                          category={exp.category || 'coffee'}
                          className="w-full h-full"
                        />
                      </div>
                      <p className="text-xs font-medium truncate">{exp.name}</p>
                      {exp.badge && (
                        <div className="mt-1 inline-block">
                          <span className="text-[10px] text-yellow-700 bg-yellow-500/10 px-1.5 py-0.5 rounded">
                            {exp.badge}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Nearby Merchant Grid - Only shown in charging state */}
      {isCharging && nearby && nearby.length > 0 && (
        <div className="pb-24 flex-shrink-0">
          <div className="grid grid-cols-2 gap-2">
            {nearby.map((merchant) => (
              <div
                key={merchant.id}
                className="bg-[#F7F8FA] rounded-xl overflow-hidden border border-[#E4E6EB] cursor-pointer"
                onClick={() => onMerchantClick(merchant)}
              >
                {/* Image */}
                <div className="relative h-[90px] sm:h-[100px] overflow-hidden">
                  {/* Use photo_urls[0] if available, fallback to photo_url, then imageUrl, then use neutral placeholder */}
                  {'photo_urls' in merchant && merchant.photo_urls && merchant.photo_urls.length > 0 ? (
                    <ImageWithFallback
                      src={merchant.photo_urls[0]}
                      alt={merchant.name}
                      category={merchant.category || 'coffee'}
                      className="w-full h-full"
                    />
                  ) : ('photo_url' in merchant && merchant.photo_url) ? (
                    <ImageWithFallback
                      src={merchant.photo_url}
                      alt={merchant.name}
                      category={merchant.category || 'coffee'}
                      className="w-full h-full"
                    />
                  ) : merchant.imageUrl ? (
                    <ImageWithFallback
                      src={merchant.imageUrl}
                      alt={merchant.name}
                      category={merchant.category || 'coffee'}
                      className="w-full h-full"
                    />
                  ) : (
                    // Neutral placeholder instead of CategoryIcon for secondary cards
                    <div className="w-full h-full bg-[#F7F8FA] flex items-center justify-center">
                      <div className="w-12 h-12 bg-[#E4E6EB] rounded-lg" />
                    </div>
                  )}

                  {/* Top-right badges on image for secondary cards */}
                  <div className="absolute top-2 right-2 flex items-center gap-1">
                    {/* Heart Icon */}
                    {likedMerchants.has(merchant.id) && (
                      <div className="w-6 h-6 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm border border-[#E4E6EB]">
                        <Heart className="w-3 h-3 text-[#1877F2] fill-[#1877F2]" />
                      </div>
                    )}
                    {/* Exclusive Badge (small star) */}
                    {'badges' in merchant && merchant.badges && merchant.badges.includes('Exclusive') && !likedMerchants.has(merchant.id) && (
                      <div className="w-6 h-6 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm border border-yellow-500/40">
                        <span className="text-xs">⭐</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Content */}
                <div className="p-2">
                  <h4 className="text-sm font-medium mb-1 line-clamp-1">{merchant.name}</h4>
                  <div className="flex items-center gap-2">
                    <div className="px-2 py-0.5 bg-[#1877F2]/10 rounded-full inline-block">
                      <span className="text-[10px] text-[#1877F2] font-medium">{merchant.walkTime}</span>
                    </div>
                    {/* Sponsored badge in content area (not on image) */}
                    {'isSponsored' in merchant && merchant.isSponsored && (
                      <div className="px-2 py-1 bg-[#F7F8FA] rounded-full border border-[#E4E6EB] flex-shrink-0">
                        <span className="text-xs text-[#65676B]">⚡ Sponsored</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation Controls */}
      <div className="sticky bottom-0 left-0 right-0 bg-white pt-3 pb-4 px-5 border-t border-[#E4E6EB] flex-shrink-0 mt-auto">
        <div className="max-w-md mx-auto">
          <div className="flex items-center justify-between">
            <button
              onClick={onPrevSet}
              className="p-3 rounded-full bg-[#F7F8FA] border border-[#E4E6EB] hover:bg-[#E4E6EB] active:scale-95 transition-all"
              aria-label="Previous set"
            >
              <ChevronLeft className="w-6 h-6 text-[#050505]" />
            </button>

            {/* Dots Indicator with micro-copy */}
            <div className="flex flex-col items-center gap-2">
              <div className="flex items-center gap-2">
                {Array.from({ length: totalSets }).map((_, index) => (
                  <div
                    key={index}
                    className={`h-2 rounded-full transition-all ${
                      index === currentSetIndex
                        ? 'w-8 bg-[#1877F2]'
                        : 'w-2 bg-[#E4E6EB]'
                    }`}
                  />
                ))}
              </div>
              <p className="text-xs text-[#65676B]">
                {isCharging ? 'More nearby while you charge' : 'More charger locations'}
              </p>
            </div>

            <button
              onClick={onNextSet}
              className="p-3 rounded-full bg-[#F7F8FA] border border-[#E4E6EB] hover:bg-[#E4E6EB] active:scale-95 transition-all"
              aria-label="Next set"
            >
              <ChevronRight className="w-6 h-6 text-[#050505]" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

