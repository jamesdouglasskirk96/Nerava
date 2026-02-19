import { Coffee, UtensilsCrossed, Wifi, Music, Trees, Bath } from "lucide-react";
import { Wc } from "@mui/icons-material";

interface PrimaryFiltersProps {
  selectedFilters: string[];
  onFilterToggle: (filter: string) => void;
}

export function PrimaryFilters({ selectedFilters, onFilterToggle }: PrimaryFiltersProps) {
  const filters = [
    { id: "coffee", label: "Coffee", icon: Coffee },
    { id: "food", label: "Food", icon: UtensilsCrossed },
    { id: "wifi", label: "WiFi", icon: Wifi },
    { id: "bathroom", label: "Bathroom", icon: Wc },
    { id: "outdoor", label: "Outdoor", icon: Trees },
    { id: "music", label: "Music", icon: Music },
  ];

  return (
    <div className="flex-shrink-0 px-4 pb-2">
      <div className="flex gap-2 justify-between">
        {filters.map((filter) => {
          const Icon = filter.icon;
          const isSelected = selectedFilters.includes(filter.id);
          
          return (
            <button
              key={filter.id}
              onClick={() => onFilterToggle(filter.id)}
              className="flex flex-col items-center gap-1.5 flex-shrink-0"
            >
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center transition-all active:scale-95 ${
                  isSelected
                    ? "bg-[#1877F2] shadow-lg"
                    : "bg-[#F7F8FA] border border-[#E4E6EB]"
                }`}
              >
                <Icon
                  className={`w-5 h-5 ${
                    isSelected ? "text-white" : "text-[#050505]"
                  }`}
                />
              </div>
              <span
                className={`text-[10px] font-medium whitespace-nowrap ${
                  isSelected ? "text-[#1877F2]" : "text-[#65676B]"
                }`}
              >
                {filter.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}