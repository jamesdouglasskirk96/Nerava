import { useState } from "react";
import { ChevronLeft, ChevronRight, Zap, Building2 } from "lucide-react";

interface Merchant {
  id: string;
  name: string;
  category?: string;
  walkTime: string;
  imageUrl: string;
  badge?: string;
  isFeatured: boolean;
}

interface Charger {
  id: string;
  name: string;
  category?: string;
  walkTime: string;
  imageUrl: string;
  distance?: string;
  availableStalls: number;
  totalStalls: number;
  experiences: Merchant[];
  network?: string;
  power?: string;
}

interface SingleChargerCardProps {
  chargers: Charger[];
  onChargerSelect: (charger: Charger) => void;
  onMerchantClick: (merchant: Merchant) => void;
}

export function SingleChargerCard({ chargers, onChargerSelect, onMerchantClick }: SingleChargerCardProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  const handlePrev = () => {
    setCurrentIndex((prev) => (prev === 0 ? chargers.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === chargers.length - 1 ? 0 : prev + 1));
  };

  const currentCharger = chargers[currentIndex];

  return (
    <div className="px-5 pt-2 pb-20">
      {/* Main Charger Card */}
      <div className="bg-white rounded-3xl overflow-hidden shadow-lg mb-6">
        {/* Charger Image */}
        <div className="relative h-44">
          <img
            src={currentCharger.imageUrl}
            alt={currentCharger.name}
            className="w-full h-full object-cover"
          />
          
          {/* Distance Badge */}
          <div className="absolute bottom-4 left-4 px-3 py-1.5 bg-black/70 backdrop-blur-sm rounded-full">
            <span className="text-xs text-white font-medium">
              {currentCharger.walkTime}
            </span>
          </div>
        </div>

        {/* Charger Info */}
        <div className="p-5">
          <h2 className="text-xl font-medium mb-3">{currentCharger.name}</h2>

          {/* Stall and Power Info */}
          <div className="flex items-center gap-4 mb-4 text-sm text-[#65676B]">
            <div className="flex items-center gap-1.5">
              <Building2 className="w-4 h-4" />
              <span>{currentCharger.totalStalls} stalls</span>
            </div>
            {currentCharger.power && (
              <div className="flex items-center gap-1.5">
                <Zap className="w-4 h-4" />
                <span>{currentCharger.power}</span>
              </div>
            )}
          </div>

          {/* Nearby Experiences Section */}
          {currentCharger.experiences.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-[#050505] mb-3">Nearby experiences</h3>
              
              <div className="grid grid-cols-2 gap-3">
                {currentCharger.experiences.slice(0, 2).map((merchant) => (
                  <button
                    key={merchant.id}
                    onClick={() => onMerchantClick(merchant)}
                    className="text-left hover:opacity-80 active:scale-98 transition-all"
                  >
                    <div className="aspect-[4/3] rounded-xl overflow-hidden mb-2">
                      <img
                        src={merchant.imageUrl}
                        alt={merchant.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <p className="text-sm font-medium line-clamp-1">{merchant.name}</p>
                  </button>
                ))}
              </div>

              {/* View All Button */}
              <button
                onClick={() => onChargerSelect(currentCharger)}
                className="w-full mt-4 py-3 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
              >
                View All Experiences
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Navigation Controls */}
      {chargers.length > 1 && (
        <>
          {/* Arrows */}
          <div className="relative flex justify-center mb-4">
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
            {chargers.map((_, index) => (
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

          {/* More Charger Locations Text */}
          <p className="text-center text-sm text-[#65676B]">
            More charger locations
          </p>
        </>
      )}
    </div>
  );
}