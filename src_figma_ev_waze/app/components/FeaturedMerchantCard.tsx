import { Zap } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

interface FeaturedMerchantCardProps {
  name: string;
  category: string;
  walkTime: string;
  imageUrl: string;
}

export function FeaturedMerchantCard({
  name,
  category,
  walkTime,
  imageUrl,
}: FeaturedMerchantCardProps) {
  return (
    <div className="bg-[#F7F8FA] rounded-2xl overflow-hidden shadow-sm border border-[#E4E6EB] active:scale-[0.99] transition-transform">
      {/* Image */}
      <div className="relative h-52 overflow-hidden">
        <ImageWithFallback
          src={imageUrl}
          alt={name}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />

        {/* Badges */}
        <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between">
          <div className="px-3 py-1.5 bg-[#1877F2] rounded-full">
            <span className="text-xs text-white">{walkTime}</span>
          </div>
          <div className="px-3 py-1.5 bg-white/90 backdrop-blur-sm rounded-full flex items-center gap-1.5 border border-[#E4E6EB]">
            <Zap className="w-3.5 h-3.5 fill-[#1877F2] text-[#1877F2]" />
            <span className="text-xs text-[#050505]">Featured while you charge</span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-center justify-between gap-2 mb-1">
          <h3 className="text-xl">{name}</h3>
          <div className="px-2.5 py-1 bg-yellow-500/10 rounded-full border border-yellow-500/20 flex-shrink-0">
            <span className="text-xs text-yellow-600">Exclusive ⭐️</span>
          </div>
        </div>
        <p className="text-sm text-[#65676B]">{category}</p>
      </div>
    </div>
  );
}