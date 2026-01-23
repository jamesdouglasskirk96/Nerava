// WhileYouCharge Screen matching Figma exactly - uses real API data
import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { UserAvatar } from '../shared/UserAvatar'
import { FeaturedMerchantCard } from './FeaturedMerchantCard'
import { Carousel } from '../shared/Carousel'
import { getAllMockMerchants } from '../../mock/mockApi'
import { useMerchantsForCharger } from '../../services/api'
import type { MerchantSummary } from '../../types'

interface WhileYouChargeScreenProps {
  chargerId?: string | null
}

export function WhileYouChargeScreen({ chargerId: propChargerId }: WhileYouChargeScreenProps = {}) {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [showTransitionMessage, setShowTransitionMessage] = useState(true)
  
  // Get charger_id from props or URL params
  const chargerId = propChargerId || searchParams.get('charger_id') || null
  
  // Fetch merchants for charger if charger_id is provided
  const { data: fetchedMerchants = [], isLoading: merchantsLoading, error: merchantsError } = useMerchantsForCharger(
    chargerId,
    { state: 'charging', open_only: false }
  )
  
  // Convert MerchantForCharger to MerchantSummary format
  const merchants = useMemo<MerchantSummary[]>(() => {
    // If we have fetched merchants, use them
    if (fetchedMerchants.length > 0) {
      return fetchedMerchants.map((m) => ({
        place_id: m.place_id || m.merchant_id || m.id,
        name: m.name,
        lat: m.lat,
        lng: m.lng,
        distance_m: m.distance_m || 0,
        types: m.types || [],
        photo_url: m.photo_url || m.logo_url,
        badges: m.is_primary || m.exclusive_title ? ['⚡ Exclusive'] : undefined,
      }))
    }
    
    // If loading, return empty array (will show loading state)
    if (merchantsLoading) {
      return []
    }
    
    // Fallback to mock data if:
    // - No charger_id provided, OR
    // - API error occurred, OR  
    // - API returned empty results
    return getAllMockMerchants()
  }, [chargerId, fetchedMerchants, merchantsLoading, merchantsError])

  // Auto-dismiss after 3 seconds
  useEffect(() => {
    if (showTransitionMessage) {
      const timer = setTimeout(() => setShowTransitionMessage(false), 3000)
      return () => clearTimeout(timer)
    }
  }, [showTransitionMessage])

  const handleMerchantClick = (placeId: string) => {
    // Navigate to merchant details with charger_id for activation flow
    const url = chargerId 
      ? `/m/${placeId}?charger_id=${chargerId}`
      : `/m/${placeId}`
    navigate(url)
  }

  const handleToggleToPreCharging = () => {
    navigate('/pre-charging')
  }

  return (
    <div className="h-[100dvh] max-h-[100dvh] bg-white flex flex-col overflow-hidden">
      {/* Header - Matching Figma: 60px height, 20px horizontal padding */}
      <header className="bg-white px-5 h-[60px] flex-shrink-0 flex items-center justify-between border-b border-[#E4E6EB] relative">
        {/* Left side: Back button */}
        <button
          onClick={handleToggleToPreCharging}
          className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center hover:bg-gray-200 active:scale-95 transition-all"
          aria-label="Back to chargers"
        >
          <ArrowLeft className="w-4 h-4 text-[#050505]" />
        </button>

        {/* Center: Logo */}
        <div className="absolute left-1/2 transform -translate-x-1/2">
          <a href="/" className="flex items-center">
            <img
              src="/nerava-logo.png"
              alt="Nerava"
              className="h-6 w-auto"
            />
          </a>
        </div>

        {/* Right side: User avatar */}
        <UserAvatar />
      </header>

      {/* Main content - Matching Figma padding: 24px horizontal, 16px top */}
      <main className="flex-1 flex flex-col overflow-y-auto min-h-0">
        <div className="flex-1 px-6 pt-3 pb-2 flex flex-col min-h-0">
          {/* Title section - More compact for mobile */}
          <div className="mb-3 space-y-0.5 flex-shrink-0">
            {/* Heading 1: Reduced size for mobile - single line */}
            <h2 
              className="text-2xl font-medium leading-7 text-[#050505] text-center whitespace-nowrap"
              style={{ letterSpacing: '0.395px', whiteSpace: 'nowrap' }}
            >
              What to do while you charge
            </h2>
            
            {/* Subtitle: 14px Regular, line-height 20px, letter-spacing -0.15px, center-aligned */}
            <p 
              className="text-xs font-normal leading-4 text-[#656A6B] text-center"
              style={{ letterSpacing: '-0.15px' }}
            >
              Curated access, active while charging
            </p>
          </div>

          {/* Carousel - Constrained to fit viewport */}
          <div className="flex-1 flex flex-col min-h-0 overflow-y-auto">
            {merchantsLoading ? (
              <div className="text-center text-[#656A6B] py-8">Loading merchants...</div>
            ) : merchants.length > 0 ? (
              <Carousel<MerchantSummary>
                items={merchants}
                renderItem={(merchant) => (
                  <FeaturedMerchantCard
                    merchant={merchant}
                    onClick={() => handleMerchantClick(merchant.place_id)}
                    expanded={true}
                  />
                )}
                transitionMessage={
                  showTransitionMessage ? (
                    <div className="text-center py-2 animate-fade-in">
                      <p className="text-sm text-[#1877F2] font-medium">
                        These businesses offer free perks while you charge
                      </p>
                    </div>
                  ) : undefined
                }
              />
            ) : (
              <div className="text-center text-[#656A6B] py-8">No merchants available</div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
