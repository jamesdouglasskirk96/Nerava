import { X, Heart, MapPin, Clock, ArrowRight, Share2, Wallet, ChevronLeft, ChevronRight, Star, ThumbsUp, ThumbsDown } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { SocialProofBadge } from "./SocialProofBadge";
import { AmenityVotes } from "./AmenityVotes";
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
  exclusiveOffer?: string; // The main exclusive offer text
  exclusiveOfferDetails?: string; // Additional details/options for exclusive
  neravaSessionsCount?: number;
  activeDriversCount?: number;
  amenities?: {
    bathroom: { upvotes: number; downvotes: number };
    wifi: { upvotes: number; downvotes: number };
  };
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
  const [userAmenityVotes, setUserAmenityVotes] = useState<{
    bathroom: 'up' | 'down' | null;
    wifi: 'up' | 'down' | null;
  }>({
    bathroom: null,
    wifi: null,
  });
  const [localAmenityCounts, setLocalAmenityCounts] = useState(merchant.amenities);
  const [showAmenityVoteModal, setShowAmenityVoteModal] = useState(false);
  const [selectedAmenity, setSelectedAmenity] = useState<'bathroom' | 'wifi' | null>(null);

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

  const fullDescription = merchant.description || "A local favorite offering great food and atmosphere.";

  const handleAmenityVote = (amenity: 'bathroom' | 'wifi', voteType: 'up' | 'down') => {
    const previousVote = userAmenityVotes[amenity];
    
    // Toggle vote if same type clicked, otherwise change vote
    const newVote = previousVote === voteType ? null : voteType;
    
    setUserAmenityVotes(prev => ({
      ...prev,
      [amenity]: newVote,
    }));
    
    // Update local counts
    if (localAmenityCounts) {
      setLocalAmenityCounts(prev => {
        if (!prev) return prev;
        
        const newCounts = { ...prev };
        const amenityData = { ...newCounts[amenity] };
        
        // Remove previous vote if exists
        if (previousVote === 'up') {
          amenityData.upvotes = Math.max(0, amenityData.upvotes - 1);
        } else if (previousVote === 'down') {
          amenityData.downvotes = Math.max(0, amenityData.downvotes - 1);
        }
        
        // Add new vote if not removing
        if (newVote === 'up') {
          amenityData.upvotes += 1;
        } else if (newVote === 'down') {
          amenityData.downvotes += 1;
        }
        
        newCounts[amenity] = amenityData;
        return newCounts;
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-[#242526] z-50">
      <div className="h-screen max-w-md mx-auto bg-white flex flex-col overflow-hidden">
        {/* Hero Image */}
        <div className="relative h-56 flex-shrink-0">
          <ImageWithFallback
            src={merchant.imageUrl}
            alt={merchant.name}
            className="w-full h-full object-cover"
          />
          
          {/* Back Button */}
          <button
            onClick={onClose}
            className="absolute top-4 left-4 w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-50 active:scale-95 transition-all"
          >
            <X className="w-5 h-5 text-[#050505]" />
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
              <div className="px-3 py-1.5 bg-white rounded-full shadow-lg">
                <span className="text-sm text-yellow-600 font-medium">{merchant.badge}</span>
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
            <p className="text-sm text-[#65676B] mb-2 flex-shrink-0">{merchant.category}</p>
          )}

          {/* Social Proof and Amenity Votes */}
          <div className="mb-4 flex-shrink-0 flex items-start justify-between gap-3">
            <SocialProofBadge
              neravaSessionsCount={merchant.neravaSessionsCount}
              activeDriversCount={merchant.activeDriversCount}
            />
            
            {localAmenityCounts && (
              <AmenityVotes
                bathroom={localAmenityCounts.bathroom}
                wifi={localAmenityCounts.wifi}
                interactive={false}
                onAmenityClick={(amenity) => {
                  setSelectedAmenity(amenity);
                  setShowAmenityVoteModal(true);
                }}
              />
            )}
          </div>

          {/* Exclusive Offer - Show prominently if it exists */}
          {merchant.exclusiveOffer && (
            <div className="bg-gradient-to-r from-yellow-500/10 to-amber-500/10 rounded-2xl p-4 mb-4 flex-shrink-0 border border-yellow-600/20">
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
          <div className="bg-[#F7F8FA] rounded-2xl p-3 mb-3 flex-shrink-0">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                <MapPin className="w-4 h-4 text-[#1877F2]" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm mb-0.5">Distance</h3>
                <p className="text-xs text-[#65676B]">
                  {merchant.distance || "0.2 miles"}
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
                      <ImageWithFallback
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
                      <div className="flex items-center gap-2 flex-wrap">
                        <div className="px-2.5 py-1 bg-[#1877F2]/10 rounded-full inline-block">
                          <span className="text-xs text-[#1877F2] font-medium">{exp.walkTime}</span>
                        </div>
                        {exp.badge && (
                          <div className="inline-block">
                            <span className="text-[10px] text-yellow-700 bg-yellow-500/10 px-2 py-1 rounded-full">{exp.badge}</span>
                          </div>
                        )}
                        {likedMerchants.has(exp.id) && (
                          <div className="w-5 h-5 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0 border border-[#1877F2]/20">
                            <Heart className="w-3 h-3 text-[#1877F2] fill-[#1877F2]" />
                          </div>
                        )}
                      </div>
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
                  {!isCharging ? "Secure a Spot after arrival" : "Secure a Spot"}
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

      {/* Amenity Vote Modal */}
      {showAmenityVoteModal && selectedAmenity && localAmenityCounts && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl p-8 max-w-sm w-full shadow-2xl">
            {/* Title */}
            <h2 className="text-xl text-center mb-4">Rate {selectedAmenity === 'bathroom' ? 'Bathroom' : 'WiFi'}</h2>

            {/* Description */}
            <p className="text-center text-[#65676B] mb-6">
              How was the {selectedAmenity === 'bathroom' ? 'bathroom' : 'WiFi'} at {merchant.name}?
            </p>

            {/* Vote Buttons */}
            <div className="flex gap-3 mb-6">
              <button
                onClick={() => {
                  handleAmenityVote(selectedAmenity, 'up');
                  setShowAmenityVoteModal(false);
                }}
                className={`flex-1 py-4 rounded-2xl font-medium transition-all flex items-center justify-center gap-2 ${
                  userAmenityVotes[selectedAmenity] === 'up'
                    ? 'bg-green-100 text-green-700 border-2 border-green-500'
                    : 'bg-[#F7F8FA] text-[#050505] border-2 border-[#E4E6EB] hover:border-green-500'
                }`}
              >
                <ThumbsUp className="w-5 h-5" />
                Good
              </button>
              <button
                onClick={() => {
                  handleAmenityVote(selectedAmenity, 'down');
                  setShowAmenityVoteModal(false);
                }}
                className={`flex-1 py-4 rounded-2xl font-medium transition-all flex items-center justify-center gap-2 ${
                  userAmenityVotes[selectedAmenity] === 'down'
                    ? 'bg-red-100 text-red-700 border-2 border-red-500'
                    : 'bg-[#F7F8FA] text-[#050505] border-2 border-[#E4E6EB] hover:border-red-500'
                }`}
              >
                <ThumbsDown className="w-5 h-5" />
                Bad
              </button>
            </div>

            {/* Cancel Button */}
            <button
              onClick={() => setShowAmenityVoteModal(false)}
              className="w-full py-3 bg-white border border-[#E4E6EB] text-[#65676B] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-98 transition-all"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}