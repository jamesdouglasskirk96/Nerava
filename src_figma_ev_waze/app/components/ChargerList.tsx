import { LiveStallIndicator } from "./LiveStallIndicator";
import { ChevronRight } from "lucide-react";

interface Charger {
  id: string;
  name: string;
  category?: string;
  walkTime: string;
  imageUrl: string;
  distance?: string;
  availableStalls: number;
  totalStalls: number;
  experiences?: any[];
  rating?: number;
}

interface ChargerListProps {
  chargers: Charger[];
  onChargerSelect: (charger: Charger) => void;
}

export function ChargerList({ chargers, onChargerSelect }: ChargerListProps) {
  return (
    <div className="px-5 py-4 space-y-3">
      {chargers.map((charger) => (
        <button
          key={charger.id}
          onClick={() => onChargerSelect(charger)}
          className="w-full bg-white border border-[#E4E6EB] rounded-2xl overflow-hidden hover:shadow-md active:scale-98 transition-all"
        >
          <div className="flex items-center gap-4 p-4">
            {/* Charger Image */}
            <div className="w-20 h-20 rounded-xl overflow-hidden flex-shrink-0 bg-[#F7F8FA]">
              <img
                src={charger.imageUrl}
                alt={charger.name}
                className="w-full h-full object-cover"
              />
            </div>

            {/* Charger Info */}
            <div className="flex-1 text-left">
              <h3 className="font-medium mb-1">{charger.name}</h3>
              
              {charger.distance && (
                <p className="text-xs text-[#65676B] mb-2">
                  {charger.distance} • {charger.walkTime}
                </p>
              )}

              {/* Live Stall Availability */}
              <LiveStallIndicator
                availableStalls={charger.availableStalls}
                totalStalls={charger.totalStalls}
              />
            </div>

            {/* Chevron */}
            <ChevronRight className="w-5 h-5 text-[#65676B] flex-shrink-0" />
          </div>
        </button>
      ))}
    </div>
  );
}
