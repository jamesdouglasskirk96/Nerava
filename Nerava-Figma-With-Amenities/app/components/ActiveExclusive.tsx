import { MapPin, Clock, Heart, Share2, Navigation, Wallet, X, QrCode } from "lucide-react";
import { useState } from "react";
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
  const [showFullscreenCode, setShowFullscreenCode] = useState(false);
  const [codeRevealed, setCodeRevealed] = useState(false);

  // Timer color based on urgency
  const getTimerColor = () => {
    if (minutes <= 5) return 'text-red-600 bg-red-50 border-red-200';
    if (minutes <= 10) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-[#050505] bg-white/95 border-[#E4E6EB]';
  };

  const handleShowHost = () => {
    setCodeRevealed(true);
    setShowFullscreenCode(true);
  };

  const getIntentLabel = () => {
    if (!refuelDetails) return null;
    
    switch (refuelDetails.intent) {
      case 'eat':
        // Map party size values to display labels
        const getPartySizeLabel = (size: number) => {
          if (size === 2) return 'Party of 1-2';
          if (size === 4) return 'Party of 3-4';
          if (size >= 5) return 'Party of 5+';
          return `Party of ${size}`;
        };
        
        return {
          primary: 'DINING',
          secondary: `(${getPartySizeLabel(refuelDetails.partySize || 2)})`
        };
      case 'work':
        return {
          primary: 'WORK SESSION',
          secondary: refuelDetails.needsPowerOutlet ? '(Power Outlet)' : ''
        };
      case 'quick-stop':
        return {
          primary: 'QUICK STOP',
          secondary: refuelDetails.isToGo ? '(To-Go)' : ''
        };
    }
  };

  return (
    <>
      <div className="fixed inset-0 bg-white z-50">
        <div className="h-screen max-w-md mx-auto bg-white flex flex-col overflow-hidden">
          {/* Hero Image - Reduced height */}
          <div className="relative h-32 flex-shrink-0">
            <img
              src={merchant.imageUrl}
              alt={merchant.name}
              className="w-full h-full object-cover"
            />
            
            {/* Status Bar */}
            <div className="absolute top-3 left-3 right-3 flex items-center justify-between">
              <button
                onClick={onClose}
                className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-50 active:scale-95 transition-all"
              >
                <X className="w-5 h-5 text-[#050505]" />
              </button>
              <div className="flex gap-2 items-center">
                <div className="px-3 py-1.5 bg-[#1877F2] rounded-full">
                  <span className="text-xs text-white font-medium">Active Session</span>
                </div>
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
              </div>
            </div>

            {/* Countdown Timer with Urgency Colors */}
            <div className="absolute bottom-3 left-3 right-3 flex justify-center">
              <div className={`px-4 py-1.5 backdrop-blur-sm rounded-full border ${getTimerColor()}`}>
                <span className="text-sm font-medium">
                  {minutes} {minutes === 1 ? 'minute' : 'minutes'} remaining
                </span>
              </div>
            </div>
          </div>

          {/* Content - No scrolling, fixed layout */}
          <div className="flex-1 px-5 py-4 flex flex-col min-h-0">
            {/* Reservation Details Card - Compact HERO ELEMENT */}
            {refuelDetails && (
              <div className="bg-gradient-to-r from-[#1877F2]/5 to-[#1877F2]/10 rounded-2xl p-3 mb-3 border-2 border-[#1877F2]/30 flex-shrink-0">
                {/* Small label */}
                <p className="text-[10px] text-[#1877F2] font-medium mb-1 text-center">YOUR RESERVATION</p>

                {/* MASSIVE Intent Text */}
                <div className="mb-1.5 text-center">
                  <p className="text-3xl font-black text-[#1877F2] tracking-tight leading-none mb-0.5">
                    {getIntentLabel()?.primary}
                  </p>
                  {getIntentLabel()?.secondary && (
                    <p className="text-xl font-bold text-[#1877F2] tracking-tight">
                      {getIntentLabel()?.secondary}
                    </p>
                  )}
                </div>

                {/* Merchant Name */}
                <p className="text-base font-medium text-center mb-1.5 text-[#050505]">{merchant.name}</p>

                {/* Instruction */}
                <p className="text-[10px] text-[#65676B] mb-1.5 text-center">
                  {codeRevealed ? 'Show this screen at the host stand' : 'Press "Show Host" button when you arrive'}
                </p>

                {/* Verification Code - Hidden until revealed */}
                {codeRevealed && (
                  <div className="bg-white rounded-xl p-2 border border-[#E4E6EB]">
                    <p className="text-[9px] text-[#65676B] mb-0.5 text-center">Reservation ID</p>
                    <p className="text-base font-mono font-bold text-center tracking-widest">
                      {verificationCode}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Exclusive Offer - Compact */}
            {merchant.exclusiveOffer && (
              <div className="bg-gradient-to-r from-yellow-500/10 to-amber-500/10 rounded-xl p-2.5 mb-3 border border-yellow-600/20 flex-shrink-0">
                <div className="flex items-start gap-2">
                  <div className="w-6 h-6 bg-yellow-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                    <Wallet className="w-3 h-3 text-yellow-700" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-[10px] mb-0.5 text-yellow-900">Bonus Offer</h3>
                    <p className="text-xs text-yellow-800 leading-snug">
                      {merchant.exclusiveOffer}
                    </p>
                    {merchant.exclusiveOfferDetails && (
                      <p className="text-[9px] text-yellow-700 mt-0.5 leading-snug">
                        {merchant.exclusiveOfferDetails}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Distance and Hours - Compact Side by Side */}
            <div className="flex gap-2 mb-3 flex-shrink-0">
              {/* Distance Info */}
              <div className="bg-[#F7F8FA] rounded-xl p-2.5 flex-1">
                <div className="flex items-start gap-1.5">
                  <div className="w-7 h-7 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                    <MapPin className="w-3.5 h-3.5 text-[#1877F2]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-[10px] mb-0.5">Distance</h3>
                    <p className="text-[9px] text-[#65676B] leading-tight">
                      {merchant.distance || "0.2 miles"} · {merchant.walkTime}
                    </p>
                  </div>
                </div>
              </div>

              {/* Hours */}
              <div className="bg-[#F7F8FA] rounded-xl p-2.5 flex-1">
                <div className="flex items-start gap-1.5">
                  <div className="w-7 h-7 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                    <Clock className="w-3.5 h-3.5 text-[#1877F2]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-[10px] mb-0.5">Hours Today</h3>
                    <p className="text-[9px] text-[#65676B] leading-tight">
                      {merchant.hours || "7:00 AM - 8:00 PM"} · {merchant.hoursStatus || "Open"}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* CTA Buttons - Push to bottom */}
            <div className="mt-auto space-y-2.5 flex-shrink-0">
              {/* SIGNATURE "SHOW HOST" BUTTON */}
              {refuelDetails && (
                <button
                  onClick={handleShowHost}
                  className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-bold text-base hover:bg-[#166FE5] active:scale-98 transition-all shadow-lg flex items-center justify-center gap-2"
                >
                  <QrCode className="w-5 h-5" />
                  Show Host
                </button>
              )}
              
              <button
                onClick={() => {
                  const merchantAddress = encodeURIComponent(merchant.name);
                  window.open(`https://www.google.com/maps/dir/?api=1&destination=${merchantAddress}`, '_blank');
                }}
                className="w-full py-3.5 bg-white border-2 border-[#1877F2] text-[#1877F2] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-98 transition-all flex items-center justify-center gap-2"
              >
                <Navigation className="w-4 h-4" />
                Get Directions
              </button>
              
              <button
                onClick={onArrived}
                className="w-full py-3.5 bg-[#F7F8FA] text-[#050505] rounded-2xl font-medium hover:bg-[#E4E6EB] active:scale-98 transition-all"
              >
                Done Charging
              </button>
              
              <button
                onClick={() => {
                  alert("Call merchant: +1 (512) 555-0123");
                }}
                className="w-full py-1.5 text-[#65676B] text-xs font-medium hover:text-[#050505] transition-colors"
              >
                Issue? Call Restaurant
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Fullscreen Verification Code Modal */}
      {showFullscreenCode && (
        <div className="fixed inset-0 bg-white z-[60] flex items-center justify-center">
          <div className="max-w-md w-full p-8">
            <button
              onClick={() => setShowFullscreenCode(false)}
              className="absolute top-6 right-6 w-12 h-12 bg-[#F7F8FA] rounded-full flex items-center justify-center hover:bg-[#E4E6EB] active:scale-95 transition-all"
            >
              <X className="w-6 h-6 text-[#050505]" />
            </button>

            {/* HERO: The "Fast Pass" Screen */}
            <div className="text-center mb-8">
              <div className="mb-6">
                <div className="w-20 h-20 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <QrCode className="w-10 h-10 text-[#1877F2]" />
                </div>
                <h1 className="text-2xl font-bold mb-2">Show this to your host</h1>
                <p className="text-sm text-[#65676B]">at {merchant.name}</p>
              </div>

              {/* MASSIVE Intent Display */}
              <div className="bg-gradient-to-r from-[#1877F2]/5 to-[#1877F2]/10 rounded-3xl p-8 mb-6 border-2 border-[#1877F2]/30">
                <p className="text-6xl font-black text-[#1877F2] tracking-tight leading-none mb-2">
                  {getIntentLabel()?.primary}
                </p>
                {getIntentLabel()?.secondary && (
                  <p className="text-3xl font-bold text-[#1877F2] tracking-tight mb-4">
                    {getIntentLabel()?.secondary}
                  </p>
                )}
                
                {/* Animated Verification Code */}
                <div className="bg-white rounded-2xl p-6 border-2 border-[#1877F2]/20 mt-4">
                  <p className="text-xs text-[#65676B] mb-2">Reservation ID</p>
                  <p className="text-2xl font-mono font-black tracking-wide text-[#050505] animate-pulse break-all">
                    {codeRevealed ? verificationCode : 'XXXX-XXXX-XXX'}
                  </p>
                </div>
              </div>

              <button
                onClick={() => {
                  navigator.clipboard.writeText(verificationCode);
                  alert('Code copied to clipboard');
                }}
                className="w-full py-4 bg-[#F7F8FA] text-[#050505] rounded-2xl font-medium hover:bg-[#E4E6EB] active:scale-98 transition-all"
              >
                Copy Code
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}