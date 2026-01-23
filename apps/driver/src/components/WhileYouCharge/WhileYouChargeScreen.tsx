// WhileYouCharge Screen matching Figma exactly
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChargingActivePill } from './ChargingActivePill'
import { FeaturedMerchantCard } from './FeaturedMerchantCard'
import { SecondaryMerchantCard } from './SecondaryMerchantCard'
import { Carousel } from '../shared/Carousel'
import { useMerchantsForCharger } from '../../services/api'
import type { MerchantSummary } from '../../types'

// Carousel item type with id for keying
type CarouselMerchant = MerchantSummary & { id: string }

export function WhileYouChargeScreen() {
  const navigate = useNavigate()

  // For Canyon Ridge charger, use the actual charger ID
  // In production, this would come from location check or charger selection
  const chargerId = 'canyon_ridge_tesla'
  
  // Fetch merchants for charger (charging state)
  const { data: fetchedMerchants = [], isLoading: merchantsLoading } = useMerchantsForCharger(
    chargerId,
    { state: 'charging', open_only: false }
  )

  // Separate primary from secondary merchants
  const { primaryMerchant, secondaryMerchants } = useMemo(() => {
    const primary = fetchedMerchants.find(m => m.is_primary) || null
    const secondary = fetchedMerchants.filter(m => !m.is_primary).slice(0, 2) // Limit to 2 secondary
    
    // No fallback to mock data - use only fetched merchants
    return {
      primaryMerchant: primary ? { ...primary, place_id: primary.id, id: primary.id } : null,
      secondaryMerchants: secondary.map(m => ({ ...m, place_id: m.id, id: m.id }))
    }
  }, [fetchedMerchants])

  // Combine primary + secondary for carousel (primary first, then secondary)
  const merchants = useMemo<CarouselMerchant[]>(() => {
    const all: CarouselMerchant[] = []
    if (primaryMerchant) {
      all.push(primaryMerchant as CarouselMerchant)
    }
    all.push(...secondaryMerchants)
    return all
  }, [primaryMerchant, secondaryMerchants])

  const handleMerchantClick = (placeId: string) => {
    navigate(`/m/${placeId}`)
  }

  const handleToggleToPreCharging = () => {
    navigate('/pre-charging')
  }

  return (
    <div className="h-[100dvh] max-h-[100dvh] bg-white flex flex-col overflow-hidden">
      {/* Header - Matching Figma: 60px height, 20px horizontal padding */}
      <header className="bg-white px-5 h-[60px] flex-shrink-0 flex items-center justify-between border-b border-[#E4E6EB] border-t-0 border-l-0 border-r-0">
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
        
        {/* Right side: Charging Active pill + Dev toggle */}
        <div className="flex items-center gap-2">
          {/* Dev control: Toggle to Pre-Charging */}
          <button
            onClick={handleToggleToPreCharging}
            className="px-2 py-1 text-xs text-[#656A6B] hover:text-[#050505] underline"
            title="Switch to Pre-Charging state"
          >
            Pre-Charging
          </button>
          <ChargingActivePill />
        </div>
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
            {merchants.length > 0 ? (
              <Carousel<CarouselMerchant>
                items={merchants}
                renderPrimary={(merchant) => (
                  <FeaturedMerchantCard
                    merchant={merchant}
                    onClick={() => handleMerchantClick(merchant.place_id)}
                  />
                )}
                renderSecondary={(merchant) => (
                  <SecondaryMerchantCard
                    merchant={merchant}
                    onClick={() => handleMerchantClick(merchant.place_id)}
                  />
                )}
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
