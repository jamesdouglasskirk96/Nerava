// Pre-charging state screen - matching Figma design
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChargerCard } from './ChargerCard'
import { Badge } from '../shared/Badge'
import { useMerchantsForCharger } from '../../services/api'
import { useDriverSessionContext } from '../../contexts/DriverSessionContext'

function PreChargingPill() {
  return (
    <Badge variant="featured" className="px-3 pt-[12.5px] pb-0">
      Pre-Charging
    </Badge>
  )
}

export function PreChargingScreen() {
  const navigate = useNavigate()
  const { locationPermission, coordinates } = useDriverSessionContext()
  
  // Hardcode to Canyon Ridge charger for primary merchant override
  const TESLA_CANYON_RIDGE_CHARGER_ID = 'canyon_ridge_tesla'
  
  // Check if location is not available (for browse mode badge)
  const isBrowseMode = !coordinates && (locationPermission === 'denied' || locationPermission === 'skipped')
  
  // Fetch merchants for Canyon Ridge charger (pre-charge state)
  // Should return ONLY the primary merchant (Asadas Grill)
  // Note: open_only=false to show merchant even if open status is unknown
  const { data: merchants = [], isLoading: merchantsLoading, error: merchantsError } = useMerchantsForCharger(
    TESLA_CANYON_RIDGE_CHARGER_ID,
    { state: 'pre-charge', open_only: false }
  )
  
  // Log for debugging
  if (merchantsError) {
    console.error('Error fetching merchants:', merchantsError)
  }
  if (merchants.length > 0) {
    console.log('Merchants received:', merchants)
  } else if (!merchantsLoading) {
    console.warn('No merchants returned for charger:', TESLA_CANYON_RIDGE_CHARGER_ID)
  }
  
  // Get the primary merchant (should be only one in pre-charge)
  const primaryMerchant = useMemo(() => {
    return merchants.find(m => m.is_primary) || merchants[0] || null
  }, [merchants])
  
  // Hardcoded charger data for Canyon Ridge
  const canyonRidgeCharger = useMemo(() => ({
    id: TESLA_CANYON_RIDGE_CHARGER_ID,
    name: 'Tesla Supercharger Canyon Ridge',
    network_name: 'Tesla',
    lat: 30.4021,
    lng: -97.7266,
    distance_m: 0,
    stalls: 12,
    plug_types: ['Tesla'],
    rating: 4.8,
    nearby_experiences: primaryMerchant ? [{
      place_id: primaryMerchant.place_id || primaryMerchant.id || '',
      name: primaryMerchant.name,
      lat: primaryMerchant.lat,
      lng: primaryMerchant.lng,
      photo_url: primaryMerchant.photo_url || primaryMerchant.photo_urls?.[0] || primaryMerchant.logo_url,
      types: primaryMerchant.types || (primaryMerchant.category ? [primaryMerchant.category] : ['restaurant']),
      distance_m: primaryMerchant.distance_m || 0,
      is_primary: primaryMerchant.is_primary,
      exclusive_title: primaryMerchant.exclusive_title,
      exclusive_description: primaryMerchant.exclusive_description,
      open_now: primaryMerchant.open_now,
      open_until: primaryMerchant.open_until,
      rating: primaryMerchant.rating,
      user_rating_count: primaryMerchant.user_rating_count,
    }] : []
  }), [primaryMerchant])

  const handleChargerClick = (chargerId: string) => {
    // TODO: Wire to backend navigation
    console.log('Navigate to charger:', chargerId)
  }

  const handleToggleToCharging = () => {
    navigate('/wyc')
  }

  return (
    <div className="h-[100dvh] max-h-[100dvh] bg-white flex flex-col overflow-hidden">
      {/* Header - Matching Figma: 60px height, 20px horizontal padding */}
      <header className="bg-white px-5 h-[60px] flex-shrink-0 flex items-center justify-between border-b border-[#E4E6EB]">
        {/* Logo: "NERAVA" + ⚡ icon - 16px font, 6px spacing */}
        <div className="flex items-center gap-1.5">
          <h1 
            className="text-base font-normal text-[#050505]"
            style={{ letterSpacing: '-0.7125px', lineHeight: '24px' }}
          >
            NERAVA
          </h1>
          <svg 
            className="w-4 h-4 text-facebook-blue" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
            strokeWidth={1.33}
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              d="M13 10V3L4 14h7v7l9-11h-7z" 
            />
          </svg>
        </div>
        
        {/* Right side: Pre-Charging pill + Dev toggle */}
        <div className="flex items-center gap-2">
          {/* Dev control: Toggle to Charging */}
          <button
            onClick={handleToggleToCharging}
            className="px-2 py-1 text-xs text-[#656A6B] hover:text-[#050505] underline"
            title="Switch to Charging state"
          >
            Charging
          </button>
          {isBrowseMode && (
            <Badge variant="default" className="text-xs">
              Browse mode
            </Badge>
          )}
          <PreChargingPill />
        </div>
      </header>

      {/* Main content - Matching Figma padding: 24px horizontal, 16px top */}
      <main className="flex-1 flex flex-col overflow-y-auto min-h-0">
        <div className="flex-1 px-6 pt-3 pb-4 flex flex-col min-h-0">
          {/* Title section - More compact for mobile */}
          <div className="mb-3 space-y-0.5 flex-shrink-0">
            {/* Heading 1: Reduced size for mobile */}
            <h2 
              className="text-2xl font-medium leading-7 text-[#050505] text-center"
              style={{ letterSpacing: '0.395px' }}
            >
              Find a charger near experiences
            </h2>
            
            {/* Subtitle: 14px Regular, line-height 20px, letter-spacing -0.15px, center-aligned */}
            <p 
              className="text-xs font-normal leading-4 text-[#656A6B] text-center"
              style={{ letterSpacing: '-0.15px' }}
            >
              Discover charging stations with great places nearby
            </p>
          </div>

          {/* Single charger card with ONLY primary merchant - no carousel, no secondary cards */}
          <div className="flex-1 flex flex-col min-h-0 overflow-y-auto">
            {primaryMerchant ? (
              <div className="space-y-3">
              <div className="transition-opacity duration-300">
                <ChargerCard
                  charger={canyonRidgeCharger}
                  onClick={() => handleChargerClick(TESLA_CANYON_RIDGE_CHARGER_ID)}
                />
                </div>
                {/* NO carousel controls - only one charger in pre-charge state */}
              </div>
            ) : merchantsLoading ? (
              <div className="text-center text-[#656A6B] py-8">Loading experiences...</div>
            ) : (
              <div className="text-center text-[#656A6B] py-8">No experiences available at this charger.</div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
