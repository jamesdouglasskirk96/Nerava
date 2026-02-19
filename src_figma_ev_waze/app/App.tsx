import { ChargerList } from "./components/ChargerList";
import { SingleChargerCard } from "./components/SingleChargerCard";
import { SingleMerchantCarousel } from "./components/SingleMerchantCarousel";
import { MerchantDetails } from "./components/MerchantDetails";
import { ActiveExclusive } from "./components/ActiveExclusive";
import { OTPModal } from "./components/OTPModal";
import { PrimaryFilters } from "./components/PrimaryFilters";
import { WalletModal } from "./components/WalletModal";
import { RefuelIntentModal, type RefuelDetails } from "./components/RefuelIntentModal";
import { SpotSecuredModal } from "./components/SpotSecuredModal";
import { Zap, Wallet, User, ArrowLeft, Share2, CheckCircle, ThumbsUp, ThumbsDown } from "lucide-react";
import { useState, useEffect } from "react";

// Function to generate unique daily visit code
const generateDailyVisitCode = (merchantName: string): string => {
  const locationCode = "ATX"; // Location code (Austin)
  const merchantCode = merchantName.toUpperCase().replace(/[^A-Z]/g, "").substring(0, 6);
  
  // Get day of year for daily reset
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 0);
  const diff = now.getTime() - start.getTime();
  const oneDay = 1000 * 60 * 60 * 24;
  const dayOfYear = Math.floor(diff / oneDay);
  
  // Generate unique number based on day of year (001-365)
  const dailyNumber = String(dayOfYear).padStart(3, "0");
  
  return `${locationCode}-${merchantCode}-${dailyNumber}`;
};

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
  neravaSessionsCount?: number;
  activeDriversCount?: number;
  amenities?: {
    bathroom: { upvotes: number; downvotes: number };
    wifi: { upvotes: number; downvotes: number };
  };
}

interface Charger {
  id: string;
  name: string;
  category?: string;
  walkTime: string;
  imageUrl: string;
  distance?: string;
  hours?: string;
  hoursStatus?: string;
  description?: string;
  availableStalls: number;
  totalStalls: number;
  experiences: Merchant[];
  rating?: number;
  network?: string;
  power?: string;
  isFeatured?: boolean;
}

// Mock chargers data with live availability and social proof
const chargers: Charger[] = [
  {
    id: "c1",
    name: "Tesla Supercharger",
    walkTime: "10 min drive",
    imageUrl: "https://images.unsplash.com/photo-1694266475815-19ded81303fd?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxUZXNsYSUyMFN1cGVyY2hhcmdlciUyMHN0YXRpb258ZW58MXx8fHwxNzY3OTc3NjYxfDA&ixlib=rb-4.1.0&q=80&w=1080",
    distance: "2.1 miles",
    hours: "24/7",
    hoursStatus: "Available now",
    description: "High-speed charging station with 16 superchargers. Located in the heart of downtown with multiple dining and shopping options nearby.",
    availableStalls: 3,
    totalStalls: 5,
    rating: 4.8,
    isFeatured: true,
    network: "Tesla",
    power: "DC",
    experiences: [
      {
        id: "e1",
        name: "Asadas Grill",
        category: "Mexican • Restaurant",
        walkTime: "3 min walk",
        imageUrl: "https://images.unsplash.com/photo-1712630514718-3830cc6c0d0a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxNZXhpY2FuJTIwcmVzdGF1cmFudCUyMGludGVyaW9yfGVufDF8fHx8MTc2Nzk3NjIzNXww&ixlib=rb-4.1.0&q=80&w=1080",
        badge: "⭐ Exclusive",
        isFeatured: true,
        distance: "0.1 miles",
        hours: "11 AM–11 PM",
        hoursStatus: "Open now",
        description: "Laid-back option with a terrace serving classic regional Mexican snacks & mains, plus happy hours.",
        exclusiveOffer: "Free beverage with any entree or alcohol",
        exclusiveOfferDetails: "Soda, Coffee, or Margarita",
        neravaSessionsCount: 128,
        activeDriversCount: 2,
        amenities: {
          bathroom: { upvotes: 42, downvotes: 3 },
          wifi: { upvotes: 38, downvotes: 7 },
        },
      },
      {
        id: "e2",
        name: "Juice Society",
        category: "Smoothies • Wellness",
        walkTime: "4 min walk",
        imageUrl: "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?w=600&q=80",
        isFeatured: false,
        neravaSessionsCount: 84,
        activeDriversCount: 1,
        amenities: {
          bathroom: { upvotes: 28, downvotes: 5 },
          wifi: { upvotes: 45, downvotes: 3 },
        },
      },
      {
        id: "e3",
        name: "Downtown Deli",
        category: "Sandwiches • Quick Bite",
        walkTime: "2 min walk",
        imageUrl: "https://images.unsplash.com/photo-1542838132-92c53300491e?w=600&q=80",
        isFeatured: false,
        neravaSessionsCount: 56,
        activeDriversCount: 0,
        amenities: {
          bathroom: { upvotes: 19, downvotes: 8 },
          wifi: { upvotes: 22, downvotes: 11 },
        },
      },
    ],
  },
  {
    id: "c2",
    name: "Riverside Charging Hub",
    walkTime: "8 min drive",
    imageUrl: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
    distance: "1.8 miles",
    hours: "6 AM - 11 PM",
    hoursStatus: "Available now",
    description: "Level 2 charging with scenic riverside views.",
    availableStalls: 2,
    totalStalls: 6,
    rating: 4.5,
    isFeatured: false,
    experiences: [
      {
        id: "e4",
        name: "Green Leaf Café",
        category: "Organic • Coffee",
        walkTime: "2 min walk",
        imageUrl: "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=800&q=80",
        isFeatured: false,
        neravaSessionsCount: 92,
        activeDriversCount: 3,
      },
      {
        id: "e5",
        name: "Wellness Studio",
        category: "Yoga • Meditation",
        walkTime: "5 min walk",
        imageUrl: "https://images.unsplash.com/photo-1545205597-3d9d02c29597?w=600&q=80",
        isFeatured: false,
        neravaSessionsCount: 47,
        activeDriversCount: 0,
      },
    ],
  },
  {
    id: "c3",
    name: "Westside Fast Charge",
    walkTime: "15 min drive",
    imageUrl: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
    distance: "3.2 miles",
    hours: "24/7",
    hoursStatus: "Available now",
    description: "Fast CCS charging in a shopping district.",
    availableStalls: 0,
    totalStalls: 4,
    rating: 4.2,
    isFeatured: false,
    experiences: [
      {
        id: "e6",
        name: "Artisan Bakery",
        category: "Pastries • Bread",
        walkTime: "3 min walk",
        imageUrl: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600&q=80",
        isFeatured: false,
        neravaSessionsCount: 63,
        activeDriversCount: 1,
      },
    ],
  },
];

export default function App() {
  // Layer state: 1 = Chargers, 2 = Merchants at Charger, 3 = Merchant Details
  const [currentLayer, setCurrentLayer] = useState<1 | 2 | 3>(1);
  const [selectedCharger, setSelectedCharger] = useState<Charger | null>(null);
  const [selectedMerchant, setSelectedMerchant] = useState<Merchant | null>(null);
  const [primaryFilters, setPrimaryFilters] = useState<string[]>([]);
  const [showWallet, setShowWallet] = useState(false);
  const [likedMerchants, setLikedMerchants] = useState<Set<string>>(new Set(["e1"]));
  
  // Exclusive flow state
  const [activeExclusive, setActiveExclusive] = useState<Merchant | null>(null);
  const [exclusiveRemainingTime, setExclusiveRemainingTime] = useState(60);
  const [isInChargerRadius, setIsInChargerRadius] = useState(true);
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [pendingExclusiveMerchant, setPendingExclusiveMerchant] = useState<Merchant | null>(null);
  const [showActivationModal, setShowActivationModal] = useState(false);
  const [showArrivalModal, setShowArrivalModal] = useState(false);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [selectedPreferences, setSelectedPreferences] = useState<string[]>([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showActiveExclusiveView, setShowActiveExclusiveView] = useState(false);
  
  // Refuel intent state
  const [showRefuelIntent, setShowRefuelIntent] = useState(false);
  const [refuelDetails, setRefuelDetails] = useState<RefuelDetails | null>(null);
  const [showSpotSecured, setShowSpotSecured] = useState(false);
  const [verificationCode, setVerificationCode] = useState<string>("");

  // Load liked merchants and check auth from localStorage on mount
  useEffect(() => {
    const storedLikes = localStorage.getItem('neravaLikes');
    if (storedLikes) {
      setLikedMerchants(new Set(JSON.parse(storedLikes)));
    }
    
    const storedAuth = localStorage.getItem('neravaAuth');
    if (storedAuth) {
      const authData = JSON.parse(storedAuth);
      if (authData.authenticated) {
        setIsAuthenticated(true);
      }
    }
  }, []);

  // Save liked merchants to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('neravaLikes', JSON.stringify(Array.from(likedMerchants)));
  }, [likedMerchants]);

  // Timer countdown for active exclusive
  useEffect(() => {
    if (activeExclusive) {
      const interval = setInterval(() => {
        setExclusiveRemainingTime((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            setShowCompletionModal(true);
            return 0;
          }
          return prev - 1;
        });
      }, 60000);

      return () => clearInterval(interval);
    }
  }, [activeExclusive]);

  const handleToggleLike = (merchantId: string) => {
    setLikedMerchants((prev) => {
      const newLikes = new Set(prev);
      if (newLikes.has(merchantId)) {
        newLikes.delete(merchantId);
      } else {
        newLikes.add(merchantId);
      }
      return newLikes;
    });
  };

  const handleFilterToggle = (filter: string) => {
    setPrimaryFilters((prev) => {
      if (prev.includes(filter)) {
        return prev.filter((f) => f !== filter);
      }
      return [...prev, filter];
    });
  };

  const handleChargerSelect = (charger: Charger) => {
    setSelectedCharger(charger);
    setCurrentLayer(2);
  };

  const handleMerchantClick = (merchant: Merchant) => {
    setSelectedMerchant(merchant);
    setCurrentLayer(3);
  };

  const handleBackToChargers = () => {
    setCurrentLayer(1);
    setSelectedCharger(null);
  };

  const handleBackToMerchants = () => {
    setCurrentLayer(2);
    setSelectedMerchant(null);
  };

  const handleActivateExclusive = (merchant: Merchant) => {
    if (!isAuthenticated) {
      setPendingExclusiveMerchant(merchant);
      setShowOTPModal(true);
    } else {
      // Show refuel intent modal instead of going straight to activation
      setShowRefuelIntent(true);
    }
  };

  const handleOTPSuccess = () => {
    setIsAuthenticated(true);
    setShowOTPModal(false);
    // Show refuel intent modal after OTP success
    setShowRefuelIntent(true);
  };

  const handleOTPClose = () => {
    setShowOTPModal(false);
    setPendingExclusiveMerchant(null);
  };

  const handleRefuelConfirm = (details: RefuelDetails) => {
    if (!selectedMerchant) return;
    
    // Store refuel details and generate verification code
    setRefuelDetails(details);
    const code = generateDailyVisitCode(selectedMerchant.name);
    setVerificationCode(code);
    
    // Close refuel intent modal and show spot secured modal
    setShowRefuelIntent(false);
    setShowSpotSecured(true);
  };

  const handleRefuelClose = () => {
    setShowRefuelIntent(false);
  };

  const handleViewWallet = () => {
    // Activate the spot and start walking flow
    setActiveExclusive(selectedMerchant);
    setExclusiveRemainingTime(60);
    setShowSpotSecured(false);
    setSelectedMerchant(null);
    setCurrentLayer(1);
    setShowActiveExclusiveView(true);
  };

  const handleStartWalking = () => {
    setActiveExclusive(selectedMerchant);
    setExclusiveRemainingTime(60);
    setShowActivationModal(false);
    setSelectedMerchant(null);
    setCurrentLayer(1);
    setShowActiveExclusiveView(true);
  };

  const handleArrived = () => {
    setShowArrivalModal(true);
  };

  const handleArrivalDone = () => {
    setShowArrivalModal(false);
    setShowCompletionModal(true);
  };

  const handleCompletionFeedback = () => {
    setShowCompletionModal(false);
    setShowPreferences(true);
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
    setActiveExclusive(null);
    setSelectedPreferences([]);
  };

  const handleShare = () => {
    setShowShareModal(true);
  };

  const copyLink = () => {
    const url = activeExclusive 
      ? `https://nerava.com/merchant/${activeExclusive.id}`
      : `https://nerava.com/merchant/${selectedMerchant?.id}`;
    navigator.clipboard.writeText(url);
    setShowShareModal(false);
  };

  // Get active and expired exclusives for wallet
  const activeExclusives = activeExclusive ? [activeExclusive] : [];
  const expiredExclusives: Merchant[] = [];

  return (
    <>
      {/* Discovery View - Always show unless viewing exclusive fullscreen */}
      {(!activeExclusive || !showActiveExclusiveView) && (
        <div className="min-h-screen bg-white text-[#050505] max-w-md mx-auto flex flex-col h-screen overflow-hidden">
          {/* Header */}
          <header className="bg-white border-b border-[#E4E6EB] flex-shrink-0">
            <div className="flex items-center justify-between px-5 py-3">
              {/* Left: Back button or Logo */}
              {currentLayer === 1 ? (
                <div className="flex items-center gap-1.5">
                  <span className="tracking-tight text-[#050505]">NERAVA</span>
                  <Zap className="w-4 h-4 fill-[#1877F2] text-[#1877F2]" />
                </div>
              ) : (
                <button
                  onClick={currentLayer === 2 ? handleBackToChargers : handleBackToMerchants}
                  className="w-10 h-10 bg-[#F7F8FA] rounded-full flex items-center justify-center hover:bg-[#E4E6EB] active:scale-95 transition-all"
                >
                  <ArrowLeft className="w-5 h-5 text-[#050505]" />
                </button>
              )}

              {/* Right: Wallet and User icons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowWallet(true)}
                  className="w-10 h-10 bg-[#F7F8FA] rounded-full flex items-center justify-center hover:bg-[#E4E6EB] active:scale-95 transition-all relative"
                >
                  <Wallet className="w-5 h-5 text-[#050505]" />
                  {activeExclusives.length > 0 && (
                    <div className="absolute top-1 right-1 w-2 h-2 bg-[#1877F2] rounded-full" />
                  )}
                </button>
                <button className="w-10 h-10 bg-[#F7F8FA] rounded-full flex items-center justify-center hover:bg-[#E4E6EB] active:scale-95 transition-all">
                  <User className="w-5 h-5 text-[#050505]" />
                </button>
              </div>
            </div>
          </header>

          {/* Moment Header */}
          <div className="text-center px-6 pt-4 pb-2 flex-shrink-0">
            <h1 className="text-2xl sm:text-3xl mb-1">
              {currentLayer === 1 && "Find a charger near experiences"}
              {currentLayer === 2 && "What to do while you charge"}
              {currentLayer === 3 && ""}
            </h1>
          </div>

          {/* Primary Filters - Show on Layer 1 and 2 */}
          {(currentLayer === 1 || currentLayer === 2) && (
            <PrimaryFilters
              selectedFilters={primaryFilters}
              onFilterToggle={handleFilterToggle}
            />
          )}

          {/* Layer 1: Chargers List */}
          {currentLayer === 1 && (
            <div className="flex-1 overflow-y-auto">
              <SingleChargerCard
                chargers={chargers}
                onChargerSelect={handleChargerSelect}
                onMerchantClick={handleMerchantClick}
              />
            </div>
          )}

          {/* Layer 2: Merchants at Charger */}
          {currentLayer === 2 && selectedCharger && (
            <div className="flex-1 overflow-y-auto">
              <SingleMerchantCarousel
                merchants={selectedCharger.experiences}
                onMerchantClick={handleMerchantClick}
                likedMerchants={likedMerchants}
                onToggleLike={handleToggleLike}
              />
            </div>
          )}

          {/* Layer 3: Merchant Details */}
          {currentLayer === 3 && selectedMerchant && (
            <MerchantDetails
              merchant={selectedMerchant}
              isCharging={true}
              isInChargerRadius={isInChargerRadius}
              onClose={handleBackToMerchants}
              onToggleLike={handleToggleLike}
              onActivateExclusive={handleActivateExclusive}
              likedMerchants={likedMerchants}
            />
          )}
        </div>
      )}

      {/* Active Exclusive View */}
      {activeExclusive && showActiveExclusiveView && (
        <ActiveExclusive
          merchant={activeExclusive}
          remainingTime={exclusiveRemainingTime}
          onArrived={handleArrived}
          onToggleLike={handleToggleLike}
          onShare={handleShare}
          isLiked={likedMerchants.has(activeExclusive.id)}
          onClose={() => setShowActiveExclusiveView(false)}
          refuelDetails={refuelDetails || undefined}
          verificationCode={verificationCode}
        />
      )}

      {/* Wallet Modal */}
      {showWallet && (
        <WalletModal
          activeExclusives={activeExclusives}
          expiredExclusives={expiredExclusives}
          onClose={() => setShowWallet(false)}
          onExclusiveClick={handleMerchantClick}
          onViewActiveExclusive={() => {
            setShowWallet(false);
            setShowActiveExclusiveView(true);
          }}
        />
      )}

      {/* Activation Modal */}
      {showActivationModal && selectedMerchant && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
            <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Wallet className="w-8 h-8 text-[#1877F2]" />
            </div>
            <h2 className="text-2xl text-center mb-3">Exclusive Activated</h2>
            <div className="flex justify-center mb-4">
              <div className="bg-[#1877F2]/10 rounded-full px-4 py-2">
                <p className="text-sm text-[#1877F2] font-medium">
                  Active while you're charging
                </p>
              </div>
            </div>
            <div className="flex justify-center mb-6">
              <div className="bg-[#F7F8FA] rounded-full px-4 py-2">
                <p className="text-sm text-[#050505]">
                  {exclusiveRemainingTime} {exclusiveRemainingTime === 1 ? 'minute' : 'minutes'} remaining
                </p>
              </div>
            </div>
            <button
              onClick={handleStartWalking}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              Start Walking
            </button>
            <button
              onClick={() => setShowActivationModal(false)}
              className="w-full py-4 bg-[#F7F8FA] text-[#050505] rounded-2xl font-medium hover:bg-[#E4E6EB] active:scale-98 transition-all mt-3"
            >
              View Details
            </button>
          </div>
        </div>
      )}

      {/* Arrival Modal */}
      {showArrivalModal && activeExclusive && (() => {
        const visitCode = generateDailyVisitCode(activeExclusive.name);
        return (
          <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
            <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
              <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-2xl text-center mb-3">You're Here</h2>
              <p className="text-center text-[#65676B] mb-4">
                Show this screen to staff at {activeExclusive.name}
              </p>
              <div className="bg-[#1877F2]/5 rounded-2xl p-4 mb-6 border-2 border-[#1877F2]/20">
                <p className="text-xs text-[#65676B] text-center mb-2">Verification Code</p>
                <p className="text-2xl font-mono font-bold text-[#1877F2] text-center tracking-wider">
                  {visitCode}
                </p>
              </div>
              <div className="bg-[#F7F8FA] rounded-2xl p-4 mb-6 border border-[#E4E6EB]">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium mb-1">{activeExclusive.name}</h3>
                    <p className="text-xs text-[#65676B]">Exclusive Active</p>
                  </div>
                  <div className="text-right">
                    {activeExclusive.badge && (
                      <div className="px-2.5 py-1 bg-yellow-500/10 rounded-full border border-yellow-500/20 inline-block">
                        <span className="text-xs text-yellow-700">{activeExclusive.badge}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={handleArrivalDone}
                className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
              >
                Done
              </button>
            </div>
          </div>
        );
      })()}

      {/* Completion Modal */}
      {showCompletionModal && activeExclusive && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
            <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-8 h-8 text-[#1877F2]" />
            </div>
            <h2 className="text-2xl text-center mb-3">Exclusive Completed</h2>
            <p className="text-center text-[#65676B] mb-6">
              Thanks for charging with Nerava
            </p>
            <div className="mb-6">
              <p className="text-center text-sm text-[#65676B] mb-3">
                Did this match what you wanted?
              </p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={handleCompletionFeedback}
                  className="w-16 h-16 bg-[#F7F8FA] rounded-full flex items-center justify-center hover:bg-green-100 active:scale-95 transition-all"
                >
                  <ThumbsUp className="w-6 h-6 text-[#65676B]" />
                </button>
                <button
                  onClick={handleCompletionFeedback}
                  className="w-16 h-16 bg-[#F7F8FA] rounded-full flex items-center justify-center hover:bg-red-100 active:scale-95 transition-all"
                >
                  <ThumbsDown className="w-6 h-6 text-[#65676B]" />
                </button>
              </div>
            </div>
            <button
              onClick={handleCompletionFeedback}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              Continue
            </button>
          </div>
        </div>
      )}

      {/* Preferences Modal - Updated to use primary filters */}
      {showPreferences && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
            <h2 className="text-xl text-center mb-6">Want better matches next time?</h2>
            <div className="flex flex-wrap gap-2 mb-6 justify-center">
              {['bathroom', 'wifi', 'coffee', 'food', 'outdoor', 'music'].map((pref) => {
                const labels: Record<string, string> = {
                  bathroom: '🚻 Bathroom',
                  wifi: '📶 WiFi',
                  coffee: '☕ Coffee',
                  food: '🍽️ Food',
                  outdoor: '🌿 Outdoor seating',
                  music: '🎵 Live music',
                };
                return (
                  <button
                    key={pref}
                    onClick={() => handlePreferenceSelect(pref)}
                    className={`px-4 py-2 rounded-full font-medium text-sm transition-all active:scale-95 ${
                      selectedPreferences.includes(pref)
                        ? 'bg-[#1877F2] text-white'
                        : 'bg-[#F7F8FA] text-[#050505] border border-[#E4E6EB]'
                    }`}
                  >
                    {labels[pref]}
                  </button>
                );
              })}
            </div>
            <button
              onClick={handlePreferencesDone}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              Done
            </button>
          </div>
        </div>
      )}

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
            <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Share2 className="w-8 h-8 text-[#1877F2]" />
            </div>
            <h2 className="text-2xl text-center mb-3">
              Share {activeExclusive?.name || selectedMerchant?.name}
            </h2>
            <p className="text-center text-[#65676B] mb-6">
              Share this link with friends
            </p>
            <button
              onClick={copyLink}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              Copy Link
            </button>
            <button
              onClick={() => setShowShareModal(false)}
              className="w-full py-4 bg-[#F7F8FA] text-[#050505] rounded-2xl font-medium hover:bg-[#E4E6EB] active:scale-98 transition-all mt-3"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* OTP Modal */}
      {showOTPModal && (
        <OTPModal
          onClose={handleOTPClose}
          onSuccess={handleOTPSuccess}
        />
      )}

      {/* Refuel Intent Modal */}
      {showRefuelIntent && selectedMerchant && (
        <RefuelIntentModal
          merchantName={selectedMerchant.name}
          onClose={handleRefuelClose}
          onConfirm={handleRefuelConfirm}
        />
      )}

      {/* Spot Secured Modal */}
      {showSpotSecured && selectedMerchant && refuelDetails && (
        <SpotSecuredModal
          merchantName={selectedMerchant.name}
          merchantBadge={selectedMerchant.badge}
          refuelDetails={refuelDetails}
          remainingMinutes={60}
          verificationCode={verificationCode}
          onViewWallet={handleViewWallet}
        />
      )}
    </>
  );
}