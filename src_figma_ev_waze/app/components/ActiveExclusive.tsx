import { MapPin, Clock, Heart, Share2, Navigation, Wallet, X } from "lucide-react";
import type { RefuelDetails } from "./RefuelIntentModal";

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
}

interface ActiveExclusiveProps {
  merchant: Merchant;
  remainingTime: number;
  onArrived: () => void;
  onToggleLike: (merchantId: string) => void;
  onShare: () => void;
  isLiked: boolean;
  onClose: () => void;
  refuelDetails?: RefuelDetails;
  verificationCode?: string;
}

export function ActiveExclusive({ 
  merchant, 
  remainingTime, 
  onArrived, 
  onToggleLike,
  onShare,
  isLiked,
  onClose,
  refuelDetails,
  verificationCode = "ATX-ASADAS-025"
}: ActiveExclusiveProps) {
  const minutes = remainingTime;

  const getIntentLabel = () => {
    if (!refuelDetails) return null;
    
    switch (refuelDetails.intent) {
      case 'eat':
        return `Dining (Party of ${refuelDetails.partySize})`;
      case 'work':
        return `Work Session${refuelDetails.needsPowerOutlet ? ' + Power Outlet' : ''}`;
      case 'quick-stop':
        return `Quick Stop${refuelDetails.isToGo ? ' (To-Go)' : ''}`;
    }
  };

  return (
    <div className="fixed inset-0 bg-white z-50">
      <div className="h-screen max-w-md mx-auto bg-white flex flex-col overflow-hidden">
        {/* Hero Image */}
        <div className="relative h-64 flex-shrink-0">
          <img
            src={merchant.imageUrl}
            alt={merchant.name}
            className="w-full h-full object-cover"
          />
          
          {/* Status Bar */}
          <div className="absolute top-4 left-4 right-4 flex items-center justify-between">
            <div className="px-3 py-1.5 bg-[#1877F2] rounded-full">
              <span className="text-xs text-white font-medium">Spot Secured</span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => onToggleLike(merchant.id)}
                className={`w-10 h-10 rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all ${
                  isLiked 
                    ? 'bg-[#1877F2] text-white' 
                    : 'bg-white text-[#050505]'
                }`}
              >
                <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
              </button>
              <button
                onClick={onShare}
                className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-50 active:scale-95 transition-all"
              >
                <Share2 className="w-5 h-5 text-[#050505]" />
              </button>
            </div>
          </div>

          {/* Countdown Timer */}
          <div className="absolute bottom-4 left-4 right-4 flex justify-center">
            <div className="px-4 py-2 bg-white/95 backdrop-blur-sm rounded-full border border-[#E4E6EB]">
              <span className="text-sm text-[#050505] font-medium">
                {minutes} {minutes === 1 ? 'minute' : 'minutes'} remaining
              </span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 px-6 py-6 overflow-y-auto flex flex-col">
          {/* Title */}
          <h1 className="text-3xl mb-1">{merchant.name}</h1>

          {/* Category */}
          {merchant.category && (
            <p className="text-sm text-[#65676B] mb-6">{merchant.category}</p>
          )}

          {/* Instruction */}
          <div className="bg-[#F7F8FA] rounded-2xl p-4 mb-4">
            <p className="text-sm text-[#050505] text-center">
              Walk to <span className="font-medium">{merchant.name}</span> and show this screen
            </p>
          </div>

          {/* Reservation Details Card */}
          {refuelDetails && (
            <div className="bg-gradient-to-r from-[#1877F2]/5 to-[#1877F2]/10 rounded-2xl p-4 mb-4 border border-[#1877F2]/20">
              <div className="mb-3">
                <h3 className="font-medium text-sm mb-1 text-[#1877F2]">Your Reservation</h3>
                <p className="text-sm text-[#050505]">{getIntentLabel()}</p>
              </div>

              {/* Verification Code */}
              <div className="bg-white rounded-xl p-3 border border-[#E4E6EB]">
                <p className="text-xs text-[#65676B] mb-1 text-center">Reservation ID</p>
                <p className="text-lg font-mono font-medium text-center tracking-wider">
                  {verificationCode}
                </p>
              </div>
            </div>
          )}

          {/* Exclusive Offer - Show prominently if it exists */}
          {merchant.exclusiveOffer && (
            <div className="bg-gradient-to-r from-yellow-500/10 to-amber-500/10 rounded-2xl p-4 mb-4 border border-yellow-600/20">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 bg-yellow-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <Wallet className="w-4 h-4 text-yellow-700" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-sm mb-0.5 text-yellow-900">Exclusive Offer</h3>
                  <p className="text-sm text-yellow-800 leading-relaxed">
                    {merchant.exclusiveOffer}
                  </p>
                  {merchant.exclusiveOfferDetails && (
                    <p className="text-xs text-yellow-700 mt-1">
                      {merchant.exclusiveOfferDetails}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Distance Info */}
          <div className="bg-[#F7F8FA] rounded-2xl p-3 mb-3">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                <MapPin className="w-4 h-4 text-[#1877F2]" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm mb-0.5">Distance</h3>
                <p className="text-xs text-[#65676B]">
                  {merchant.distance || "0.2 miles"} · {merchant.walkTime}
                </p>
              </div>
            </div>
          </div>

          {/* Hours */}
          <div className="bg-[#F7F8FA] rounded-2xl p-3 mb-6">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                <Clock className="w-4 h-4 text-[#1877F2]" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm mb-0.5">Hours Today</h3>
                <p className="text-xs text-[#65676B]">
                  {merchant.hours || "7:00 AM - 8:00 PM"} · {merchant.hoursStatus || "Open now"}
                </p>
              </div>
            </div>
          </div>

          {/* CTA Button */}
          <div className="mt-auto space-y-3">
            <button
              onClick={() => {
                // Open Google Maps with directions to merchant
                // In production, use actual merchant coordinates
                const merchantAddress = encodeURIComponent(merchant.name);
                window.open(`https://www.google.com/maps/dir/?api=1&destination=${merchantAddress}`, '_blank');
              }}
              className="w-full py-4 bg-white border-2 border-[#1877F2] text-[#1877F2] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-98 transition-all flex items-center justify-center gap-2"
            >
              <Navigation className="w-5 h-5" />
              Get Directions
            </button>
            <button
              onClick={onArrived}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              I'm at the Merchant
            </button>
          </div>
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-50 active:scale-95 transition-all"
        >
          <X className="w-5 h-5 text-[#050505]" />
        </button>
      </div>
    </div>
  );
}