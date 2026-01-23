import { MerchantCarousel } from "./components/MerchantCarousel";
import { MerchantDetails } from "./components/MerchantDetails";
import { ActiveExclusive } from "./components/ActiveExclusive";
import { OTPModal } from "./components/OTPModal";
import { Zap, Wallet, Share2, CheckCircle, ThumbsUp, ThumbsDown } from "lucide-react";
import { useState, useEffect } from "react";

// Personalization data - in production, this would come from user profile/session
const userProfile = {
  carName: "Tesla",
  preference: "neutral", // could be: "wellness", "adventure", "relaxation", etc.
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
  exclusiveOffer?: string; // The actual exclusive offer text
  experiences?: Merchant[]; // For chargers, attached experiences
  rating?: number; // Nerava rating for chargers
  isLiked?: boolean; // Track if user has liked this merchant
}

interface MerchantSet {
  featured: Merchant;
  nearby: Merchant[];
}

// Merchant sets - each rotation shows 1 featured + 2 nearby
const merchantSets: MerchantSet[] = [
  {
    featured: {
      id: "1",
      name: "Austin Java",
      category: "Coffee • Bakery",
      walkTime: "3 min walk",
      imageUrl: "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=800&q=80",
      badge: "⭐ Exclusive",
      isFeatured: true,
      distance: "0.2 miles",
      hours: "7:00 AM - 8:00 PM",
      hoursStatus: "Open now",
      description: "A local favorite offering premium coffee, fresh pastries, and a welcoming atmosphere. Free WiFi available for remote workers.",
      exclusiveOffer: "Free pastry with any coffee purchase",
    },
    nearby: [
      {
        id: "2",
        name: "Juice Society",
        category: "Smoothies • Wellness",
        walkTime: "4 min walk",
        imageUrl: "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?w=600&q=80",
        isFeatured: false,
        badge: "⭐",
        distance: "0.3 miles",
        hours: "8:00 AM - 6:00 PM",
        hoursStatus: "Open now",
        description: "Fresh pressed juices and organic smoothies made to order. Perfect for a healthy boost.",
      },
      {
        id: "3",
        name: "The Bookshop",
        category: "Books • Gifts",
        walkTime: "On your way out",
        imageUrl: "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=600&q=80",
        isFeatured: false,
        distance: "0.1 miles",
        hours: "9:00 AM - 9:00 PM",
        hoursStatus: "Open now",
        description: "Independent bookstore with curated selections and unique gifts. Browse our cozy reading nooks.",
      },
    ],
  },
  {
    featured: {
      id: "4",
      name: "Green Leaf Café",
      category: "Organic • Coffee",
      walkTime: "5 min walk",
      imageUrl: "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=800&q=80",
      isFeatured: true,
      distance: "0.4 miles",
      hours: "8:00 AM - 6:00 PM",
      hoursStatus: "Open now",
      description: "Organic café with a focus on sustainable practices. Enjoy a variety of coffee drinks and light bites.",
    },
    nearby: [
      {
        id: "5",
        name: "Artisan Bakery",
        category: "Pastries • Bread",
        walkTime: "3 min walk",
        imageUrl: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600&q=80",
        isFeatured: false,
        distance: "0.2 miles",
        hours: "7:00 AM - 7:00 PM",
        hoursStatus: "Open now",
        description: "Artisan bakery known for its handcrafted pastries and breads. Perfect for a quick snack.",
      },
      {
        id: "6",
        name: "Wellness Studio",
        category: "Yoga • Meditation",
        walkTime: "6 min walk",
        imageUrl: "https://images.unsplash.com/photo-1545205597-3d9d02c29597?w=600&q=80",
        isFeatured: false,
        distance: "0.5 miles",
        hours: "9:00 AM - 6:00 PM",
        hoursStatus: "Open now",
        description: "Wellness studio offering yoga classes and meditation sessions. Ideal for stress relief.",
      },
    ],
  },
  {
    featured: {
      id: "7",
      name: "Urban Grounds",
      category: "Coffee • Work Space",
      walkTime: "2 min walk",
      imageUrl: "https://images.unsplash.com/photo-1511920170033-f8396924c348?w=800&q=80",
      badge: "⭐ Free WiFi",
      isFeatured: true,
      distance: "0.1 miles",
      hours: "8:00 AM - 6:00 PM",
      hoursStatus: "Open now",
      description: "Cozy coffee shop with a dedicated workspace area. Perfect for remote workers and freelancers.",
    },
    nearby: [
      {
        id: "8",
        name: "Fresh Market",
        category: "Groceries • Deli",
        walkTime: "4 min walk",
        imageUrl: "https://images.unsplash.com/photo-1542838132-92c53300491e?w=600&q=80",
        isFeatured: false,
        distance: "0.3 miles",
        hours: "7:00 AM - 8:00 PM",
        hoursStatus: "Open now",
        description: "Local grocery store with a deli section offering fresh sandwiches and salads.",
      },
      {
        id: "9",
        name: "Vinyl Records",
        category: "Music • Vintage",
        walkTime: "5 min walk",
        imageUrl: "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?w=600&q=80",
        isFeatured: false,
        distance: "0.4 miles",
        hours: "10:00 AM - 6:00 PM",
        hoursStatus: "Open now",
        description: "Vinyl record store with a wide selection of classic and modern albums. Perfect for music enthusiasts.",
      },
    ],
  },
];

// Charger sets for pre-charging state - each charger has attached experiences
const chargerSets: MerchantSet[] = [
  {
    featured: {
      id: "c1",
      name: "Downtown Tesla Supercharger",
      category: "8 stalls • CCS & Tesla",
      walkTime: "10 min drive",
      imageUrl: "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=800&q=80",
      isFeatured: true,
      distance: "2.1 miles",
      hours: "24/7",
      hoursStatus: "Available now",
      description: "High-speed charging station with 8 superchargers. Located in the heart of downtown with multiple dining and shopping options nearby.",
      experiences: [
        {
          id: "e1",
          name: "Austin Java",
          category: "Coffee • 3 min walk",
          walkTime: "3 min walk",
          imageUrl: "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=600&q=80",
          isFeatured: false,
          badge: "⭐ Exclusive",
        },
        {
          id: "e2",
          name: "Juice Society",
          category: "Smoothies • 4 min walk",
          walkTime: "4 min walk",
          imageUrl: "https://images.unsplash.com/photo-1622597467836-f3285f2131b8?w=600&q=80",
          isFeatured: false,
        },
        {
          id: "e3",
          name: "Downtown Deli",
          category: "Sandwiches • 2 min walk",
          walkTime: "2 min walk",
          imageUrl: "https://images.unsplash.com/photo-1542838132-92c53300491e?w=600&q=80",
          isFeatured: false,
        },
        {
          id: "e4",
          name: "Book Nook",
          category: "Bookstore • 5 min walk",
          walkTime: "5 min walk",
          imageUrl: "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&q=80",
          isFeatured: false,
        },
        {
          id: "e5",
          name: "Artisan Bakery",
          category: "Pastries • 4 min walk",
          walkTime: "4 min walk",
          imageUrl: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=600&q=80",
          isFeatured: false,
        },
      ],
      rating: 4.8,
    },
    nearby: [
      {
        id: "c2",
        name: "Riverside Charging Hub",
        category: "6 stalls • Level 2",
        walkTime: "8 min drive",
        imageUrl: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
        isFeatured: false,
        distance: "1.8 miles",
      },
      {
        id: "c3",
        name: "Westside Fast Charge",
        category: "4 stalls • CCS",
        walkTime: "15 min drive",
        imageUrl: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
        isFeatured: false,
        distance: "3.2 miles",
      },
    ],
  },
  {
    featured: {
      id: "c4",
      name: "Lakeside EV Station",
      category: "10 stalls • Universal",
      walkTime: "12 min drive",
      imageUrl: "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=800&q=80",
      isFeatured: true,
      distance: "3.5 miles",
      hours: "24/7",
      hoursStatus: "Available now",
      description: "Premium charging facility with covered stalls and amenities. Adjacent to lakeside park with walking trails.",
      experiences: [
        {
          id: "e3",
          name: "Green Leaf Café",
          category: "Organic • 2 min walk",
          walkTime: "2 min walk",
          imageUrl: "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=600&q=80",
          isFeatured: false,
        },
        {
          id: "e4",
          name: "Wellness Studio",
          category: "Yoga • 5 min walk",
          walkTime: "5 min walk",
          imageUrl: "https://images.unsplash.com/photo-1545205597-3d9d02c29597?w=600&q=80",
          isFeatured: false,
        },
        {
          id: "e6",
          name: "Lakeside Trail",
          category: "Walking • 3 min walk",
          walkTime: "3 min walk",
          imageUrl: "https://images.unsplash.com/photo-1551632811-561732d1e306?w=600&q=80",
          isFeatured: false,
        },
        {
          id: "e7",
          name: "Fresh Poke Bar",
          category: "Healthy Bowls • 4 min walk",
          walkTime: "4 min walk",
          imageUrl: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&q=80",
          isFeatured: false,
        },
        {
          id: "e8",
          name: "Vintage Market",
          category: "Shopping • 6 min walk",
          walkTime: "6 min walk",
          imageUrl: "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&q=80",
          isFeatured: false,
        },
      ],
      rating: 4.5,
    },
    nearby: [
      {
        id: "c5",
        name: "North Plaza Chargers",
        category: "5 stalls • Tesla",
        walkTime: "18 min drive",
        imageUrl: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
        isFeatured: false,
        distance: "4.1 miles",
      },
      {
        id: "c6",
        name: "Central Park Station",
        category: "8 stalls • Level 2",
        walkTime: "11 min drive",
        imageUrl: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
        isFeatured: false,
        distance: "2.9 miles",
      },
    ],
  },
];

// Dynamic messaging based on featured content type
const getPersonalizedMessage = (featuredType: string, preference: string) => {
  const messages: Record<string, Record<string, string>> = {
    coffee: {
      neutral: "Curated access based on your preferences",
      wellness: "Fuel up while you charge.",
      relaxation: "Treat yourself to a moment.",
    },
    juice: {
      neutral: "Your turn to recharge.",
      wellness: "Time for a refresh.",
      relaxation: "A healthy pause for you.",
    },
    shopping: {
      neutral: "A little retail therapy?",
      wellness: "Treat yourself while you wait.",
      relaxation: "Time to browse and unwind.",
    },
    bookstore: {
      neutral: "Time to explore and unwind.",
      wellness: "Feed your mind too.",
      relaxation: "A little escape while you wait.",
    },
  };

  return messages[featuredType]?.[preference] || "Here's what fits your charge.";
};

export default function App() {
  const [currentSetIndex, setCurrentSetIndex] = useState(0);
  const [selectedMerchant, setSelectedMerchant] = useState<Merchant | null>(null);
  const [isCharging, setIsCharging] = useState(true);
  const [likedMerchants, setLikedMerchants] = useState<Set<string>>(new Set());
  
  // Exclusive flow state
  const [activeExclusive, setActiveExclusive] = useState<Merchant | null>(null);
  const [exclusiveRemainingTime, setExclusiveRemainingTime] = useState(60);
  const [isInChargerRadius, setIsInChargerRadius] = useState(true); // Mock - in production, based on geolocation
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [pendingExclusiveMerchant, setPendingExclusiveMerchant] = useState<Merchant | null>(null);
  const [showActivationModal, setShowActivationModal] = useState(false);
  const [showArrivalModal, setShowArrivalModal] = useState(false);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [selectedPreferences, setSelectedPreferences] = useState<string[]>([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Load liked merchants and check auth from localStorage on mount
  useEffect(() => {
    const storedLikes = localStorage.getItem('neravaLikes');
    if (storedLikes) {
      setLikedMerchants(new Set(JSON.parse(storedLikes)));
    }
    
    // Check if user is already authenticated
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
            // Auto-complete exclusive when timer hits 0
            setShowCompletionModal(true);
            return 0;
          }
          return prev - 1;
        });
      }, 60000); // Update every minute

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

  // Reset to first set when switching modes
  const handleToggleCharging = () => {
    setIsCharging(!isCharging);
    setCurrentSetIndex(0);
    // Reset exclusive state when switching modes
    setActiveExclusive(null);
  };

  const activeSets = isCharging ? merchantSets : chargerSets;

  const handlePrevSet = () => {
    setCurrentSetIndex((prev) => (prev === 0 ? activeSets.length - 1 : prev - 1));
  };

  const handleNextSet = () => {
    setCurrentSetIndex((prev) => (prev === activeSets.length - 1 ? 0 : prev + 1));
  };

  const handleMerchantClick = (merchant: Merchant) => {
    setSelectedMerchant(merchant);
  };

  const handleCloseMerchantDetails = () => {
    setSelectedMerchant(null);
  };

  // Exclusive flow handlers
  const handleActivateExclusive = (merchant: Merchant) => {
    // Check if user is authenticated
    if (!isAuthenticated) {
      // Show OTP modal first
      setPendingExclusiveMerchant(merchant);
      setShowOTPModal(true);
    } else {
      // User is already authenticated, proceed directly to activation
      setShowActivationModal(true);
    }
  };

  const handleOTPSuccess = () => {
    // User successfully authenticated
    setIsAuthenticated(true);
    setShowOTPModal(false);
    
    // Proceed to activation modal
    setShowActivationModal(true);
  };

  const handleOTPClose = () => {
    setShowOTPModal(false);
    setPendingExclusiveMerchant(null);
  };

  const handleStartWalking = () => {
    setActiveExclusive(selectedMerchant);
    setExclusiveRemainingTime(60);
    setShowActivationModal(false);
    setSelectedMerchant(null);
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
    // Reset state and return to discovery
    setActiveExclusive(null);
    setSelectedPreferences([]);
  };

  const handleShare = () => {
    setShowShareModal(true);
  };

  const copyLink = () => {
    const url = activeExclusive 
      ? `https://nerava.com/merchant/${activeExclusive.id}`
      : `https://nerava.com/charger/${selectedMerchant?.id}`;
    navigator.clipboard.writeText(url);
    setShowShareModal(false);
  };

  // Determine featured type based on current set
  const featuredType = "coffee"; // This would be dynamic based on featured merchant
  const personalizedMessage = getPersonalizedMessage(featuredType, userProfile.preference);

  // State-based headline and subheadline
  const headline = "What to do while you charge";
  
  const subheadline = isCharging
    ? "Curated access, active while charging"
    : "Personalized access during your charge window";
  
  return (
    <>
      {/* Discovery View - Hidden when exclusive is active */}
      {!activeExclusive && (
        <div className="min-h-screen bg-white text-[#050505] max-w-md mx-auto flex flex-col h-screen overflow-hidden">
          {/* Status Header */}
          <header className="bg-white border-b border-[#E4E6EB] flex-shrink-0">
            <div className="flex items-center justify-between px-5 py-3">
              <div className="flex items-center gap-1.5">
                <span className="tracking-tight text-[#050505]">NERAVA</span>
                <Zap className="w-4 h-4 fill-[#1877F2] text-[#1877F2]" />
              </div>
              <button
                onClick={handleToggleCharging}
                className="px-3 py-1.5 bg-[#1877F2] rounded-full hover:bg-[#166FE5] active:scale-95 transition-all"
              >
                <span className="text-xs text-white">
                  {isCharging ? "Charging Active" : "Pre-Charging"}
                </span>
              </button>
            </div>
          </header>

          {/* Moment Header */}
          <div className="text-center px-6 pt-4 pb-1 flex-shrink-0">
            <h1 className="text-2xl sm:text-3xl mb-1 whitespace-nowrap">{headline}</h1>
            <p className="text-sm text-[#65676B] whitespace-nowrap">
              {subheadline}
            </p>
          </div>

          {/* Merchant Carousel */}
          <div className="flex-1 overflow-hidden">
            <MerchantCarousel 
              merchantSet={activeSets[currentSetIndex]}
              isCharging={isCharging}
              onPrevSet={handlePrevSet}
              onNextSet={handleNextSet}
              currentSetIndex={currentSetIndex}
              totalSets={activeSets.length}
              onMerchantClick={handleMerchantClick}
              likedMerchants={likedMerchants}
            />
          </div>
        </div>
      )}

      {/* Active Exclusive View - Replaces discovery */}
      {activeExclusive && (
        <ActiveExclusive
          merchant={activeExclusive}
          remainingTime={exclusiveRemainingTime}
          onArrived={handleArrived}
          onToggleLike={handleToggleLike}
          onShare={handleShare}
          isLiked={likedMerchants.has(activeExclusive.id)}
        />
      )}

      {/* Merchant Details Modal */}
      {selectedMerchant && (
        <MerchantDetails
          merchant={selectedMerchant}
          isCharging={isCharging}
          isInChargerRadius={isInChargerRadius}
          onClose={handleCloseMerchantDetails}
          onToggleLike={handleToggleLike}
          onActivateExclusive={handleActivateExclusive}
          likedMerchants={likedMerchants}
          onExperienceClick={handleMerchantClick}
        />
      )}

      {/* Activation Modal */}
      {showActivationModal && selectedMerchant && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
            {/* Icon */}
            <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Wallet className="w-8 h-8 text-[#1877F2]" />
            </div>

            {/* Title */}
            <h2 className="text-2xl text-center mb-3">Exclusive Activated</h2>

            {/* Status */}
            <div className="flex justify-center mb-4">
              <div className="bg-[#1877F2]/10 rounded-full px-4 py-2">
                <p className="text-sm text-[#1877F2] font-medium">
                  Active while you're charging
                </p>
              </div>
            </div>

            {/* Countdown */}
            <div className="flex justify-center mb-6">
              <div className="bg-[#F7F8FA] rounded-full px-4 py-2">
                <p className="text-sm text-[#050505]">
                  {exclusiveRemainingTime} {exclusiveRemainingTime === 1 ? 'minute' : 'minutes'} remaining
                </p>
              </div>
            </div>

            {/* Buttons */}
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
      {showArrivalModal && activeExclusive && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
            {/* Icon */}
            <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>

            {/* Title */}
            <h2 className="text-2xl text-center mb-3">You're Here</h2>

            {/* Description */}
            <p className="text-center text-[#65676B] mb-6">
              Show this screen to staff at {activeExclusive.name}
            </p>

            {/* Pass Card */}
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

            {/* Button */}
            <button
              onClick={handleArrivalDone}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              Done
            </button>
          </div>
        </div>
      )}

      {/* Completion Modal */}
      {showCompletionModal && activeExclusive && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
            {/* Icon */}
            <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-8 h-8 text-[#1877F2]" />
            </div>

            {/* Title */}
            <h2 className="text-2xl text-center mb-3">Exclusive Completed</h2>

            {/* Description */}
            <p className="text-center text-[#65676B] mb-6">
              Thanks for charging with Nerava
            </p>

            {/* Feedback */}
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

            {/* Button */}
            <button
              onClick={handleCompletionFeedback}
              className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
            >
              Continue
            </button>
          </div>
        </div>
      )}

      {/* Preferences Modal */}
      {showPreferences && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
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
              {['Kids', 'Accessibility'].map((pref) => (
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

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
            {/* Icon */}
            <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Share2 className="w-8 h-8 text-[#1877F2]" />
            </div>

            {/* Title */}
            <h2 className="text-2xl text-center mb-3">
              Share {activeExclusive?.name || selectedMerchant?.name}
            </h2>

            {/* Description */}
            <p className="text-center text-[#65676B] mb-6">
              Share this link with friends
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
    </>
  );
}