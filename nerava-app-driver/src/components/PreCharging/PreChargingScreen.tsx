// Pre-charging state screen - matching Figma design, uses real data from API
import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChargerCard } from './ChargerCard'
import { CarouselControls } from '../shared/CarouselControls'
import { UserAvatar } from '../shared/UserAvatar'
import { getAllMockChargers } from '../../mock/mockApi'
import type { DiscoveryCharger } from '../../api/chargers'
import type { ChargerWithExperiences } from '../../mock/types'

interface PreChargingScreenProps {
  chargers?: DiscoveryCharger[]
  loading?: boolean
}

// Convert ChargerWithExperiences to DiscoveryCharger format
function convertMockCharger(mockCharger: ChargerWithExperiences): DiscoveryCharger {
  return {
    id: mockCharger.id,
    name: mockCharger.name,
    address: '', // Not in mock data
    lat: 0, // Not in mock data
    lng: 0, // Not in mock data
    distance_m: mockCharger.distance_m,
    drive_time_min: Math.round(mockCharger.distance_m / 1000), // Approximate: 1km per minute
    network: mockCharger.network_name || 'Unknown',
    stalls: mockCharger.stalls,
    kw: 150, // Default kW for superchargers
    photo_url: mockCharger.photo_url || '',
    nearby_merchants: mockCharger.nearby_experiences.map((merchant) => ({
      place_id: merchant.place_id,
      name: merchant.name,
      photo_url: merchant.photo_url || '',
      distance_m: merchant.distance_m,
      walk_time_min: Math.round(merchant.distance_m / 80), // 80m per minute
      has_exclusive: merchant.badges?.includes('Exclusive') || false,
    })),
  }
}

export function PreChargingScreen({ chargers: propChargers, loading: propLoading }: PreChargingScreenProps = {}) {
  const navigate = useNavigate()
  const [currentIndex, setCurrentIndex] = useState(0)
  
  // Use props if provided, otherwise convert mock data (for route usage)
  const chargers = useMemo(() => {
    if (propChargers) return propChargers
    const mockChargers = getAllMockChargers()
    return mockChargers.map(convertMockCharger)
  }, [propChargers])
  
  const loading = propLoading || false
  
  const currentCharger = chargers[currentIndex]

  const handleChargerClick = (chargerId: string) => {
    // Navigate to WhileYouChargeScreen with charger_id
    navigate(`/wyc?charger_id=${chargerId}`)
  }

  const handleToggleToCharging = () => {
    navigate('/wyc')
  }

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? chargers.length - 1 : prev - 1))
  }

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === chargers.length - 1 ? 0 : prev + 1))
  }

  const handleDotClick = (index: number) => {
    setCurrentIndex(index)
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
        
        {/* Right side: User avatar */}
        <UserAvatar />
      </header>

      {/* Main content - Matching Figma padding: 24px horizontal, 16px top */}
      <main className="flex-1 flex flex-col overflow-y-auto min-h-0">
        <div className="flex-1 px-6 pt-3 pb-2 flex flex-col min-h-0">
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

          {/* Single charger card - no secondary cards for pre-charging */}
          <div className="flex-1 flex flex-col min-h-0 overflow-y-auto">
            {loading ? (
              <div className="text-center text-[#656A6B] py-8">Loading chargers...</div>
            ) : currentCharger ? (
              <div className="flex flex-col h-full">
                <div className="flex-1 min-h-0">
                  <div className="h-full transition-opacity duration-300">
                    <ChargerCard
                      charger={currentCharger}
                      onClick={() => handleChargerClick(currentCharger.id)}
                      expanded={true}
                    />
                  </div>
                </div>

                {/* Controls */}
                {chargers.length > 1 && (
                  <CarouselControls
                    currentIndex={currentIndex}
                    totalItems={chargers.length}
                    onPrevious={handlePrevious}
                    onNext={handleNext}
                    onDotClick={handleDotClick}
                    className="flex-shrink-0"
                    labelText="More charger locations"
                  />
                )}
              </div>
            ) : (
              <div className="text-center text-[#656A6B] py-8">No chargers available</div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
