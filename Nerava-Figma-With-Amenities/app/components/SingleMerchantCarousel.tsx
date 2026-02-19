import { useState } from "react";
import { Heart, ChevronLeft, ChevronRight } from "lucide-react";
import { SocialProofBadge } from "./SocialProofBadge";
import { AmenityVotes } from "./AmenityVotes";

interface Merchant {
  id: string;
  name: string;
  category?: string;
  walkTime: string;
  imageUrl: string;
  badge?: string;
  isFeatured: boolean;
  distance?: string;
  hours?: string;
  hoursStatus?: string;
  description?: string;
  exclusiveOffer?: string;
  exclusiveOfferDetails?: string;
  neravaSessionsCount?: number;
  activeDriversCount?: number;
  amenities?: {
    bathroom: { upvotes: number; downvotes: number };
    wifi: { upvotes: number; downvotes: number };
  };
}

interface SingleMerchantCarouselProps {
  merchants: Merchant[];
  onMerchantClick: (merchant: Merchant) => void;
  likedMerchants: Set<string>;
  onToggleLike: (merchantId: string) => void;
}

export function SingleMerchantCarousel({
  merchants,
  onMerchantClick,
  likedMerchants,
  onToggleLike,
}: SingleMerchantCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev === 0 ? merchants.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === merchants.length - 1 ? 0 : prev + 1));
  };

  const currentMerchant = merchants[currentIndex];

  return (
    <div className="px-5 pt-2 pb-20">
      {/* Single Large Card */}
      <div className="relative">
        <div
          onClick={() => onMerchantClick(currentMerchant)}
          className="w-full bg-white rounded-3xl overflow-hidden shadow-lg hover:shadow-xl active:scale-98 transition-all cursor-pointer"
        >
          {/* Hero Image */}
          <div className="relative h-64">
            <img
              src={currentMerchant.imageUrl}
              alt={currentMerchant.name}
              className="w-full h-full object-cover"
            />

            {/* Walk Time and Exclusive Badge */}
            <div className="absolute bottom-4 left-4">
              <div className="px-3 py-1.5 bg-black/70 backdrop-blur-sm rounded-full">
                <span className="text-xs text-white font-medium">
                  {currentMerchant.walkTime}
                </span>
              </div>
            </div>
            
            {currentMerchant.badge && (
              <div className="absolute bottom-4 right-4">
                <div className="px-2.5 py-1 bg-white backdrop-blur-sm rounded-full shadow-lg">
                  <span className="text-xs text-yellow-600 font-medium">
                    {currentMerchant.badge}
                  </span>
                </div>
              </div>
            )}

            {/* Live Activity Indicator */}
            {currentMerchant.activeDriversCount && currentMerchant.activeDriversCount > 0 && (
              <div className="absolute top-4 left-4">
                <div className="px-2.5 py-1.5 bg-green-600/90 backdrop-blur-sm rounded-full shadow-lg flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
                  <span className="text-xs text-white font-medium">
                    {currentMerchant.activeDriversCount} here now
                  </span>
                </div>
              </div>
            )}

            {/* Like Button */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleLike(currentMerchant.id);
              }}
              className={`absolute top-4 right-4 w-10 h-10 rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all ${
                likedMerchants.has(currentMerchant.id)
                  ? "bg-[#1877F2] text-white"
                  : "bg-white text-[#050505]"
              }`}
            >
              <Heart
                className={`w-5 h-5 ${
                  likedMerchants.has(currentMerchant.id) ? "fill-current" : ""
                }`}
              />
            </button>
          </div>

          {/* Content */}
          <div className="p-5">
            {/* Title */}
            <h3 className="text-xl font-medium text-center mb-2">{currentMerchant.name}</h3>

            {/* Category */}
            {currentMerchant.category && (
              <p className="text-sm text-[#65676B] mb-3">
                {currentMerchant.category}
              </p>
            )}

            {/* Social Proof and Amenity Votes */}
            <div className="flex items-start justify-between gap-3">
              <SocialProofBadge
                neravaSessionsCount={currentMerchant.neravaSessionsCount}
                activeDriversCount={currentMerchant.activeDriversCount}
              />
              
              {currentMerchant.amenities && (
                <AmenityVotes
                  bathroom={currentMerchant.amenities.bathroom}
                  wifi={currentMerchant.amenities.wifi}
                  interactive={false}
                />
              )}
            </div>

            {/* Exclusive Offer */}
            {currentMerchant.exclusiveOffer && (
              <div className="mt-3 text-sm text-[#1877F2] font-medium">
                {currentMerchant.exclusiveOffer}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      {merchants.length > 1 && (
        <>
          {/* Arrows */}
          <div className="relative flex justify-center mb-4 mt-6">
            <button
              onClick={handlePrev}
              className="absolute left-0 w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:bg-gray-50 active:scale-95 transition-all"
            >
              <ChevronLeft className="w-6 h-6 text-[#050505]" />
            </button>
            
            <button
              onClick={handleNext}
              className="absolute right-0 w-12 h-12 bg-white rounded-full shadow-lg flex items-center justify-center hover:bg-gray-50 active:scale-95 transition-all"
            >
              <ChevronRight className="w-6 h-6 text-[#050505]" />
            </button>
          </div>

          {/* Pagination Dots */}
          <div className="flex justify-center gap-2 mb-2">
            {merchants.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentIndex(index)}
                className={`h-1.5 rounded-full transition-all ${
                  index === currentIndex
                    ? "w-6 bg-[#1877F2]"
                    : "w-1.5 bg-[#E4E6EB]"
                }`}
              />
            ))}
          </div>

          {/* More Experiences Text */}
          <p className="text-center text-sm text-[#65676B]">
            More experiences nearby
          </p>
        </>
      )}
    </div>
  );
}