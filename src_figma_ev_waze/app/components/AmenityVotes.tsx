import { Wifi, ThumbsUp, ThumbsDown } from "lucide-react";
import { Wc } from "@mui/icons-material";

interface AmenityVotesProps {
  bathroom: { upvotes: number; downvotes: number };
  wifi: { upvotes: number; downvotes: number };
  interactive?: boolean;
  userVotes?: {
    bathroom: 'up' | 'down' | null;
    wifi: 'up' | 'down' | null;
  };
  onVote?: (amenity: 'bathroom' | 'wifi', voteType: 'up' | 'down') => void;
  onAmenityClick?: (amenity: 'bathroom' | 'wifi') => void;
}

export function AmenityVotes({
  bathroom,
  wifi,
  interactive = false,
  userVotes,
  onVote,
  onAmenityClick,
}: AmenityVotesProps) {
  const amenities = [
    { 
      key: 'bathroom' as const, 
      icon: Wc, 
      label: 'WC', 
      data: bathroom 
    },
    { 
      key: 'wifi' as const, 
      icon: Wifi, 
      label: 'WiFi', 
      data: wifi 
    },
  ];

  return (
    <div className="flex items-start gap-3">
      {amenities.map(({ key, icon: Icon, label, data }) => (
        <button
          key={key}
          onClick={(e) => {
            e.stopPropagation();
            if (!interactive && onAmenityClick) {
              onAmenityClick(key);
            }
          }}
          className={`flex flex-col items-center gap-1 ${!interactive && onAmenityClick ? 'cursor-pointer hover:opacity-80 active:scale-95 transition-all' : ''}`}
        >
          {/* Icon on top */}
          <Icon className="w-4 h-4 text-[#65676B]" style={{ fontSize: '16px' }} />
          
          {/* Vote counts below */}
          {interactive ? (
            <div className="flex flex-col gap-0.5">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onVote?.(key, 'up');
                }}
                className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded-md transition-all ${
                  userVotes?.[key] === 'up' 
                    ? 'bg-green-100 text-green-700' 
                    : 'hover:bg-[#F7F8FA] text-[#65676B]'
                }`}
              >
                <ThumbsUp className="w-3 h-3" />
                <span className="text-xs font-medium">{data.upvotes}</span>
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onVote?.(key, 'down');
                }}
                className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded-md transition-all ${
                  userVotes?.[key] === 'down' 
                    ? 'bg-red-100 text-red-700' 
                    : 'hover:bg-[#F7F8FA] text-[#65676B]'
                }`}
              >
                <ThumbsDown className="w-3 h-3" />
                <span className="text-xs font-medium">{data.downvotes}</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <div className="flex items-center gap-0.5">
                <ThumbsUp className="w-2.5 h-2.5 text-green-600" />
                <span className="text-[10px] text-[#65676B] font-medium">{data.upvotes}</span>
              </div>
              <div className="flex items-center gap-0.5">
                <ThumbsDown className="w-2.5 h-2.5 text-red-600" />
                <span className="text-[10px] text-[#65676B] font-medium">{data.downvotes}</span>
              </div>
            </div>
          )}
        </button>
      ))}
    </div>
  );
}