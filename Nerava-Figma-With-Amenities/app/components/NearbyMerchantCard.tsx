import { ImageWithFallback } from "./figma/ImageWithFallback";
import { Zap } from "lucide-react";

interface NearbyMerchantCardProps {
  name: string;
  walkTime: string;
  imageUrl: string;
  isFeatured?: boolean;
}

export function NearbyMerchantCard({
  name,
  walkTime,
  imageUrl,
  isFeatured = false,
}: NearbyMerchantCardProps) {
  return (
    <div className="bg-[#F7F8FA] rounded-2xl overflow-hidden shadow-sm border border-[#E4E6EB] active:scale-[0.97] transition-transform">
      {/* Image */}
      <div className="relative h-24 overflow-hidden">
        <ImageWithFallback
          src={imageUrl}
          alt={name}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent" />
      </div>

      {/* Content */}
      <div className="p-3">
        <div className="flex items-center gap-1.5 mb-1.5">
          <h4 className="text-sm line-clamp-1">{name}</h4>
          {isFeatured && (
            <div className="flex-shrink-0 p-1 bg-white backdrop-blur-sm rounded-full border border-[#E4E6EB]">
              <Zap className="w-3 h-3 fill-[#1877F2] text-[#1877F2]" />
            </div>
          )}
        </div>
        <div className="inline-block px-2.5 py-1 bg-[#1877F2]/10 rounded-full border border-[#1877F2]/20">
          <span className="text-xs text-[#1877F2]">{walkTime}</span>
        </div>
      </div>
    </div>
  );
}