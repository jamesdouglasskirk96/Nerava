import { ArrowLeft, MapPin, Clock, Wallet, ChevronLeft, ChevronRight, Heart, Share2 } from "lucide-react";
import { useState, useEffect } from "react";

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
  experiences?: Merchant[]; // For chargers, attached experiences
  rating?: number; // Nerava rating for chargers
  exclusiveOffer?: string; // Exclusive offer for chargers
}

interface MerchantDetailsProps {
  merchant: Merchant;
  isCharging: boolean;
  isInChargerRadius: boolean;
  onClose: () => void;
  onToggleLike: (merchantId: string) => void;
  onActivateExclusive: (merchant: Merchant) => void;
  likedMerchants: Set<string>;
  onExperienceClick?: (experience: Merchant) => void;
}

export function MerchantDetails({ merchant, isCharging, isInChargerRadius, onClose, onToggleLike, onActivateExclusive, likedMerchants, onExperienceClick }: MerchantDetailsProps) {
  const [showWalletConfirm, setShowWalletConfirm] = useState(false);
  const [experienceIndex, setExperienceIndex] = useState(0);
  const [showShareModal, setShowShareModal] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [isFirstActivation, setIsFirstActivation] = useState(true);
  const [selectedPreferences, setSelectedPreferences] = useState<string[]>([]);
  const [activationTime, setActivationTime] = useState<number | null>(null);
  const [remainingMinutes, setRemainingMinutes] = useState(60);

  // Sync like state with the global liked merchants
  const isLiked = likedMerchants.has(merchant.id);

  // Check for existing activation on mount
  useEffect(() => {
    const storedActivations = localStorage.getItem('neravaActivations');
    if (storedActivations) {
      const activations = JSON.parse(storedActivations);
      const merchantActivation = activations[merchant.id];
      if (merchantActivation) {
        setActivationTime(merchantActivation);
        // Calculate remaining time
        const elapsed = Date.now() - merchantActivation;
        const remaining = Math.max(0, 60 - Math.floor(elapsed / 60000));
        setRemainingMinutes(remaining);
      }
    }
  }, [merchant.id]);

  // Update remaining time every minute
  useEffect(() => {
    if (activationTime) {
      const interval = setInterval(() => {
        const elapsed = Date.now() - activationTime;
        const remaining = Math.max(0, 60 - Math.floor(elapsed / 60000));
        setRemainingMinutes(remaining);
        
        // Clear activation if expired
        if (remaining === 0) {
          const storedActivations = localStorage.getItem('neravaActivations');
          if (storedActivations) {
            const activations = JSON.parse(storedActivations);
            delete activations[merchant.id];
            localStorage.setItem('neravaActivations', JSON.stringify(activations));
          }
          setActivationTime(null);
        }
      }, 60000); // Update every minute
      
      return () => clearInterval(interval);
    }
  }, [activationTime, merchant.id]);

  const handleAddToWallet = () => {
    // Store activation time
    const now = Date.now();
    setActivationTime(now);
    setRemainingMinutes(60);
    
    // Persist to localStorage
    const storedActivations = localStorage.getItem('neravaActivations');
    const activations = storedActivations ? JSON.parse(storedActivations) : {};
    activations[merchant.id] = now;
    localStorage.setItem('neravaActivations', JSON.stringify(activations));
    
    setShowWalletConfirm(true);
  };

  const handleDone = () => {
    setShowWalletConfirm(false);
    if (isFirstActivation) {
      setIsFirstActivation(false);
      setShowPreferences(true);
    } else {
      onClose();
    }
  };

  const handlePreferenceSelect = (preference: string) => {
    setSelectedPreferences((prev) => {
      if (prev.includes(preference)) {
        return prev.filter((p) => p !== preference);
      }
      return [...prev, preference];
    });
  };

  const handlePreferencesDone = () => {
    setShowPreferences(false);
    onClose();
  };

  const toggleLike = () => {
    onToggleLike(merchant.id);
  };

  const handleShare = () => {
    setShowShareModal(true);
  };

  const closeShareModal = () => {
    setShowShareModal(false);
  };

  const copyLink = () => {
    // In production, this would copy the actual link
    navigator.clipboard.writeText(`https://nerava.com/${isCharging ? 'merchant' : 'charger'}/${merchant.id}`);
    setShowShareModal(false);
  };

  const handlePrevExperiences = () => {
    if (merchant.experiences && merchant.experiences.length > 2) {
      setExperienceIndex((prev) => 
        prev === 0 ? Math.max(0, merchant.experiences!.length - 2) : Math.max(0, prev - 2)
      );
    }
  };

  const handleNextExperiences = () => {
    if (merchant.experiences && merchant.experiences.length > 2) {
      setExperienceIndex((prev) => 
        prev + 2 >= merchant.experiences!.length ? 0 : prev + 2
      );
    }
  };

  // Dynamic font size for titles to ensure single line
  const getTitleFontSize = (name: string) => {
    const length = name.length;
    if (length <= 20) return '1.875rem'; // text-3xl
    if (length <= 25) return '1.75rem';  // text-[1.75rem]
    if (length <= 30) return '1.5rem';   // text-2xl
    if (length <= 35) return '1.25rem';  // text-xl
    return '1.125rem'; // text-lg
  };

  // Full description text - in production this would come from the merchant data
  const fullDescription = merchant.description 
    ? `${merchant.description}\n\nLocated in the heart of downtown, this establishment has been serving the community for over 10 years. We pride ourselves on quality ingredients, exceptional service, and creating a welcoming atmosphere for all our guests.\n\nOur menu features locally sourced ingredients and changes seasonally to ensure the freshest options. Whether you're stopping by for a quick bite or settling in for a longer stay, you'll find comfortable seating, free WiFi, and a friendly team ready to serve you.\n\nWe offer various seating options including outdoor patio seating (weather permitting), cozy indoor booths, and bar seating with a view of our preparation area. Group reservations are welcome for parties of 6 or more.`
    : "A local favorite offering premium coffee, fresh pastries, and a welcoming atmosphere. Free WiFi available for remote workers.";

  const shortDescription = merchant.description || "A local favorite offering premium coffee, fresh pastries, and a welcoming atmosphere. Free WiFi a...";

  return (
    <div className="fixed inset-0 bg-[#242526] z-50">
      <div className="h-screen max-w-md mx-auto bg-white flex flex-col overflow-hidden">
        {/* Hero Image */}
        <div className="relative h-56 flex-shrink-0">
          <img
            src={merchant.imageUrl}
            alt={merchant.name}
            className="w-full h-full object-cover"
          />
          
          {/* Back Button */}
          <button
            onClick={onClose}
            className="absolute top-4 left-4 w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-50 active:scale-95 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-[#050505]" />
          </button>

          {/* Action Buttons - Heart and Share */}
          <div className="absolute top-4 right-4 flex gap-2">
            <button
              onClick={toggleLike}
              className={`w-10 h-10 rounded-full flex items-center justify-center shadow-lg hover:scale-105 active:scale-95 transition-all ${
                isLiked 
                  ? 'bg-[#1877F2] text-white' 
                  : 'bg-white text-[#050505]'
              }`}
            >
              <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
            </button>
            <button
              onClick={handleShare}
              className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-50 active:scale-95 transition-all"
            >
              <Share2 className="w-5 h-5 text-[#050505]" />
            </button>
          </div>

          {/* Walk Time Badge */}
          <div className="absolute bottom-4 left-4">
            <div className="px-3 py-1.5 bg-[#1877F2] rounded-full">
              <span className="text-sm text-white font-medium">{merchant.walkTime}</span>
            </div>
          </div>

          {/* Exclusive Badge - positioned under favorite button */}
          {merchant.badge && (
            <div className="absolute bottom-4 right-4">
              <div className="px-3 py-1.5 bg-white rounded-full border border-yellow-500/30 shadow-lg">
                <span className="text-sm text-yellow-700 font-medium">{merchant.badge}</span>
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 px-6 py-5 overflow-hidden flex flex-col">
          {/* Title */}
          <div className="mb-1 flex-shrink-0">
            <h1 className="text-3xl inline whitespace-nowrap overflow-hidden text-ellipsis max-w-full" style={{
              fontSize: getTitleFontSize(merchant.name)
            }}>{merchant.name}</h1>
          </div>

          {/* Category */}
          {merchant.category && (
            <p className="text-sm text-[#65676B] mb-3 flex-shrink-0">{merchant.category}</p>
          )}

          {/* Exclusive Offer - Show prominently if it exists */}
          {merchant.exclusiveOffer && (
            <div className="bg-gradient-to-r from-yellow-500/10 to-amber-500/10 rounded-2xl p-4 mb-4 flex-shrink-0 border border-yellow-600/20">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 bg-yellow-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <Wallet className="w-4 h-4 text-yellow-700" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-sm mb-0.5 text-yellow-900">Exclusive Offer</h3>
                  <p className="text-sm text-yellow-800">
                    {merchant.exclusiveOffer}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Distance Info */}
          <div className="bg-[#F7F8FA] rounded-2xl p-3 mb-3 flex-shrink-0">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                <MapPin className="w-4 h-4 text-[#1877F2]" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm mb-0.5">Distance</h3>
                <p className="text-xs text-[#65676B]">
                  {merchant.distance || "0.2 miles"} · Fits your charge window
                </p>
              </div>
            </div>
          </div>

          {/* Hours */}
          <div className="bg-[#F7F8FA] rounded-2xl p-3 mb-4 flex-shrink-0">
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

          {/* Description - Only show for merchants in charging state */}
          {isCharging && (
            <div className="mb-5 flex-shrink-0">
              <div className="text-sm text-[#65676B] leading-relaxed max-h-32 overflow-y-auto pr-2">
                <p className="whitespace-pre-line">
                  {fullDescription}
                </p>
              </div>
            </div>
          )}

          {/* Nearby Experiences - 2-card grid with navigation (for chargers only) */}
          {!isCharging && merchant.experiences && merchant.experiences.length > 0 && (
            <div className="mb-5 flex-shrink-0">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-sm">Nearby Experiences</h3>
                {merchant.experiences.length > 2 && (
                  <div className="flex gap-2">
                    <button
                      onClick={handlePrevExperiences}
                      className="w-7 h-7 bg-[#1877F2]/10 rounded-full flex items-center justify-center hover:bg-[#1877F2]/20 active:scale-95 transition-all"
                    >
                      <ChevronLeft className="w-4 h-4 text-[#1877F2]" />
                    </button>
                    <button
                      onClick={handleNextExperiences}
                      className="w-7 h-7 bg-[#1877F2]/10 rounded-full flex items-center justify-center hover:bg-[#1877F2]/20 active:scale-95 transition-all"
                    >
                      <ChevronRight className="w-4 h-4 text-[#1877F2]" />
                    </button>
                  </div>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                {merchant.experiences.slice(experienceIndex, experienceIndex + 2).map((exp) => (
                  <div
                    key={exp.id}
                    className="bg-[#F7F8FA] rounded-xl overflow-hidden border border-[#E4E6EB] cursor-pointer hover:border-[#1877F2] transition-colors"
                    onClick={() => onExperienceClick && onExperienceClick(exp)}
                  >
                    <div className="relative h-28 overflow-hidden">
                      <img
                        src={exp.imageUrl}
                        alt={exp.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="p-3">
                      <h4 className="text-sm font-medium mb-1 truncate">{exp.name}</h4>
                      {exp.category && (
                        <p className="text-xs text-[#65676B] mb-2 truncate">{exp.category}</p>
                      )}
                      <div className="px-2.5 py-1 bg-[#1877F2]/10 rounded-full inline-block">
                        <span className="text-xs text-[#1877F2] font-medium">{exp.walkTime}</span>
                      </div>
                      {exp.badge && (
                        <div className="mt-2">
                          <span className="text-[10px] text-yellow-700 bg-yellow-500/10 px-2 py-1 rounded-full">{exp.badge}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CTA Buttons */}
          <div className="flex flex-col gap-3 flex-shrink-0 mt-auto">
            <button className="w-full py-3.5 bg-white border-2 border-[#1877F2] text-[#1877F2] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-98 transition-all">
              {isCharging ? "Get Directions" : "Navigate to Charger"}
            </button>
            {merchant.badge && (
              <div className="relative">
                <button
                  onClick={() => isCharging && isInChargerRadius && onActivateExclusive(merchant)}
                  disabled={!isCharging || !isInChargerRadius}
                  className={`w-full py-3.5 rounded-2xl font-medium transition-all flex items-center justify-center gap-2 ${
                    isCharging && isInChargerRadius
                      ? 'bg-[#1877F2] text-white hover:bg-[#166FE5] active:scale-98'
                      : 'bg-[#E4E6EB] text-[#65676B] cursor-not-allowed'
                  }`}
                >
                  <Wallet className="w-5 h-5" />
                  {!isCharging ? "Activate after arrival" : "Activate Exclusive"}
                </button>
                {!isCharging && (
                  <p className="text-xs text-[#65676B] text-center mt-2">
                    Available once you arrive and start charging
                  </p>
                )}
                {isCharging && !isInChargerRadius && (
                  <p className="text-xs text-[#65676B] text-center mt-2">
                    Available once you start charging
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Wallet Confirmation Modal */}
      {showWalletConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
            {/* Icon */}
            <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Wallet className="w-8 h-8 text-[#1877F2]" />
            </div>

            {/* Title */}
            <h2 className="text-2xl text-center mb-3">Exclusive Activated</h2>

            {/* Time remaining - centered */}
            <div className="flex justify-center mb-4">
              <div className="bg-[#1877F2]/10 rounded-full px-4 py-2">
                <p className="text-sm text-[#1877F2] font-medium">
                  Active for the next {remainingMinutes} {remainingMinutes === 1 ? 'minute' : 'minutes'}
                </p>
              </div>
            </div>

            {/* Description */}
            <p className="text-center text-[#65676B] mb-6">
              Exclusive is active while you're charging.<br />
              Show it at {merchant.name}.
            </p>

            {/* Pass Card */}
            <div className="bg-[#F7F8FA] rounded-2xl p-4 mb-6 border border-[#E4E6EB]">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium mb-1">{merchant.name}</h3>
                </div>
                <div className="text-right">
                  {merchant.badge && (
                    <div className="px-2.5 py-1 bg-yellow-500/10 rounded-full border border-yellow-500/20 inline-block">
                      <span className="text-xs text-yellow-700">{merchant.badge}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Done Button */}
            <button
              onClick={handleDone}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              View Wallet
            </button>
          </div>
        </div>
      )}

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
            {/* Icon */}
            <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Share2 className="w-8 h-8 text-[#1877F2]" />
            </div>

            {/* Title */}
            <h2 className="text-2xl text-center mb-3">Share {merchant.name}</h2>

            {/* Description */}
            <p className="text-center text-[#65676B] mb-6">
              Share this link with friends to let them know about {merchant.name}.
            </p>

            {/* Copy Link Button */}
            <button
              onClick={copyLink}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              Copy Link
            </button>

            {/* Close Button */}
            <button
              onClick={closeShareModal}
              className="w-full py-4 bg-gray-200 text-gray-700 rounded-2xl font-medium hover:bg-gray-300 active:scale-98 transition-all mt-3"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Preferences Modal */}
      {showPreferences && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
            {/* Title */}
            <h2 className="text-xl text-center mb-6">Want better matches next time?</h2>

            {/* Preference Chips - Row 1 */}
            <div className="flex flex-wrap gap-2 mb-3 justify-center">
              {['Coffee', 'Food', 'Fitness', 'Retail', 'Pets'].map((pref) => (
                <button
                  key={pref}
                  onClick={() => handlePreferenceSelect(pref)}
                  className={`px-4 py-2 rounded-full font-medium text-sm transition-all active:scale-95 ${
                    selectedPreferences.includes(pref)
                      ? 'bg-[#1877F2] text-white'
                      : 'bg-[#F7F8FA] text-[#050505] border border-[#E4E6EB]'
                  }`}
                >
                  {pref}
                </button>
              ))}
            </div>

            {/* Preference Chips - Row 2 */}
            <div className="flex flex-wrap gap-2 mb-3 justify-center">
              {['Kids', 'Pets', 'Accessibility'].map((pref) => (
                <button
                  key={pref}
                  onClick={() => handlePreferenceSelect(pref)}
                  className={`px-4 py-2 rounded-full font-medium text-sm transition-all active:scale-95 ${
                    selectedPreferences.includes(pref)
                      ? 'bg-[#1877F2] text-white'
                      : 'bg-[#F7F8FA] text-[#050505] border border-[#E4E6EB]'
                  }`}
                >
                  {pref}
                </button>
              ))}
            </div>

            {/* Preference Chips - Row 3 */}
            <div className="flex flex-wrap gap-2 mb-6 justify-center">
              {['Morning', 'Midday', 'Evening'].map((pref) => (
                <button
                  key={pref}
                  onClick={() => handlePreferenceSelect(pref)}
                  className={`px-4 py-2 rounded-full font-medium text-sm transition-all active:scale-95 ${
                    selectedPreferences.includes(pref)
                      ? 'bg-[#1877F2] text-white'
                      : 'bg-[#F7F8FA] text-[#050505] border border-[#E4E6EB]'
                  }`}
                >
                  {pref}
                </button>
              ))}
            </div>

            {/* Done Button */}
            <button
              onClick={handlePreferencesDone}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}