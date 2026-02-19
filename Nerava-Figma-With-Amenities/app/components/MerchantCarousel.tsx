import { ChevronLeft, ChevronRight, Heart } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

interface Merchant {
  id: string;
  name: string;
  category?: string;
  walkTime: string;
  imageUrl: string;
  badge?: string;
  isFeatured: boolean;
  experiences?: Merchant[]; // For chargers, attached experiences
  rating?: number; // Nerava rating for chargers
  isLiked?: boolean; // Track if user has liked this merchant
}

interface MerchantSet {
  featured: Merchant;
  nearby: Merchant[];
}

interface MerchantCarouselProps {
  merchantSet: MerchantSet;
  isCharging: boolean;
  onPrevSet: () => void;
  onNextSet: () => void;
  currentSetIndex: number;
  totalSets: number;
  onMerchantClick: (merchant: Merchant) => void;
  likedMerchants: Set<string>;
}

export function MerchantCarousel({ 
  merchantSet, 
  isCharging, 
  onPrevSet, 
  onNextSet,
  currentSetIndex,
  totalSets,
  onMerchantClick,
  likedMerchants
}: MerchantCarouselProps) {
  const { featured, nearby } = merchantSet;

  // Dynamic font size for charger titles to ensure single line
  const getTitleFontSize = (name: string) => {
    const length = name.length;
    if (length <= 20) return "text-2xl";
    if (length <= 25) return "text-xl";
    if (length <= 30) return "text-lg";
    return "text-base";
  };

  return (
    <div className="relative h-full flex flex-col justify-start pt-3 px-5">
      {/* Featured Merchant Card */}
      <div className="mb-4">
        <div 
          className="bg-[#F7F8FA] rounded-2xl overflow-hidden shadow-md border border-[#E4E6EB] cursor-pointer"
          onClick={() => onMerchantClick(featured)}
        >
          {/* Image */}
          <div className="relative h-64 overflow-hidden">
            <ImageWithFallback
              src={featured.imageUrl}
              alt={featured.name}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />

            {/* Walk Time Badge on Image */}
            <div className="absolute bottom-3 left-3">
              <div className="px-3 py-1.5 bg-[#1877F2] rounded-full">
                <span className="text-xs text-white font-medium">{featured.walkTime}</span>
              </div>
            </div>

            {/* Sponsored Badge on Image */}
            {isCharging && featured.isFeatured && (
              <div className="absolute bottom-3 right-3">
                <div className="px-3 py-1.5 bg-white/90 backdrop-blur-sm rounded-full border border-[#E4E6EB]">
                  <span className="text-xs text-[#65676B] font-medium">⚡ Sponsored</span>
                </div>
              </div>
            )}
          </div>

          {/* Content */}
          <div className="p-5">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <h3 className={getTitleFontSize(featured.name)}>{featured.name}</h3>
                {isCharging && featured.isFeatured && (
                  <p className="text-xs text-[#65676B] mt-1">
                    {featured.badge?.includes('Exclusive') ? 'Free Beverage Exclusive' : `Brought to you by ${featured.name}`}
                  </p>
                )}
                {!isCharging && featured.isFeatured && (
                  <p className="text-xs text-[#65676B] mt-1">Popular charging destination</p>
                )}
              </div>
              <div className="flex items-center gap-1.5">
                {featured.badge && (
                  <div className="px-2.5 py-1 bg-gradient-to-r from-yellow-500/15 to-amber-500/15 rounded-full border border-yellow-600/30 flex-shrink-0">
                    <span className="text-xs font-medium text-yellow-700">{featured.badge}</span>
                  </div>
                )}
                {likedMerchants.has(featured.id) && (
                  <div className="w-7 h-7 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0 border border-[#1877F2]/20">
                    <Heart className="w-4 h-4 text-[#1877F2] fill-[#1877F2]" />
                  </div>
                )}
              </div>
            </div>
            {featured.category && (
              <p className="text-sm text-[#65676B] mt-1">{featured.category}</p>
            )}
            
            {/* Nerava Rating for chargers */}
            {!isCharging && featured.rating && (
              <div className="flex items-center gap-1.5 mt-2">
                <span className="text-xs text-[#65676B]">Nerava rating:</span>
                <div className="flex items-center gap-0.5">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <span key={index} className={index < featured.rating! ? "text-yellow-500" : "text-[#E4E6EB]"}>
                      ★
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {/* Experiences for chargers (pre-charging mode) */}
            {!isCharging && featured.experiences && featured.experiences.length > 0 && (
              <div className="mt-4 pt-4 border-t border-[#E4E6EB]">
                <p className="text-xs text-[#65676B] mb-2">Nearby experiences:</p>
                <div className="flex gap-2">
                  {featured.experiences.slice(0, 2).map((exp) => (
                    <div key={exp.id} className="flex-1 bg-white rounded-lg p-2 border border-[#E4E6EB]">
                      <div className="relative h-16 rounded overflow-hidden mb-1.5">
                        <ImageWithFallback
                          src={exp.imageUrl}
                          alt={exp.name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <p className="text-xs font-medium truncate">{exp.name}</p>
                      <div className="flex items-center gap-1 mt-1">
                        {exp.badge && (
                          <div className="inline-block">
                            <span className="text-[10px] text-yellow-700 bg-yellow-500/10 px-1.5 py-0.5 rounded">{exp.badge}</span>
                          </div>
                        )}
                        {likedMerchants.has(exp.id) && (
                          <div className="w-4 h-4 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0 border border-[#1877F2]/20">
                            <Heart className="w-2.5 h-2.5 text-[#1877F2] fill-[#1877F2]" />
                          </div>
                        )}
                      </div>
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
        <div className="pb-32">
          <div className="grid grid-cols-2 gap-3">
            {nearby.map((merchant) => (
              <div
                key={merchant.id}
                className="bg-[#F7F8FA] rounded-2xl overflow-hidden border border-[#E4E6EB] cursor-pointer"
                onClick={() => onMerchantClick(merchant)}
              >
                {/* Image */}
                <div className="relative h-[123px] overflow-hidden">
                  <ImageWithFallback
                    src={merchant.imageUrl}
                    alt={merchant.name}
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* Content */}
                <div className="p-3">
                  <h4 className="text-base mb-1.5">{merchant.name}</h4>
                  <div className="flex items-center gap-2">
                    <div className="px-2.5 py-1 bg-[#1877F2]/10 rounded-full inline-block">
                      <span className="text-xs text-[#1877F2] font-medium">{merchant.walkTime}</span>
                    </div>
                    {/* Badge priority: 1. Liked, 2. Exclusive, 3. Sponsored */}
                    {likedMerchants.has(merchant.id) ? (
                      <div className="w-6 h-6 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0 border border-[#1877F2]/20">
                        <Heart className="w-3.5 h-3.5 text-[#1877F2] fill-[#1877F2]" />
                      </div>
                    ) : merchant.badge ? (
                      <div className="px-2 py-1 bg-gradient-to-r from-yellow-500/15 to-amber-500/15 rounded-full border border-yellow-600/30 flex-shrink-0">
                        <span className="text-xs">{merchant.badge}</span>
                      </div>
                    ) : merchant.isFeatured ? (
                      <div className="px-2 py-1 bg-[#F7F8FA] rounded-full border border-[#E4E6EB] flex-shrink-0">
                        <span className="text-xs text-[#65676B]">⚡ Sponsored</span>
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation Controls */}
      <div className="absolute bottom-0 left-0 right-0 bg-white pt-4 pb-6 px-5 border-t border-[#E4E6EB]">
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
                        ? "w-8 bg-[#1877F2]"
                        : "w-2 bg-[#E4E6EB]"
                    }`}
                  />
                ))}
              </div>
              <p className="text-xs text-[#65676B]">
                {isCharging ? "More nearby while you charge" : "More charger locations"}
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
  );
}