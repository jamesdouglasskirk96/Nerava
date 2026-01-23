// Pre-charging state screen - uses real data from API only
import { useState, useMemo, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChargerCard } from './ChargerCard'
import { CarouselControls } from '../shared/CarouselControls'
import { UserAvatar } from '../shared/UserAvatar'
import { useGeolocation } from '../../hooks/useGeolocation'
import { getChargerDiscovery, type DiscoveryCharger } from '../../api/chargers'

interface PreChargingScreenProps {
  chargers?: DiscoveryCharger[]
  loading?: boolean
}

export function PreChargingScreen({ chargers: propChargers, loading: propLoading }: PreChargingScreenProps = {}) {
  const navigate = useNavigate()
  const [currentIndex, setCurrentIndex] = useState(0)
  const geo = useGeolocation()

  // Fetch chargers from API if not provided via props
  const [fetchedChargers, setFetchedChargers] = useState<DiscoveryCharger[]>([])
  const [fetchLoading, setFetchLoading] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const hasFetchedRef = useRef(false)

  useEffect(() => {
    // Only fetch once when location becomes available for the first time
    if (
      !hasFetchedRef.current &&
      (!propChargers || propChargers.length === 0) &&
      geo.lat &&
      geo.lng &&
      !geo.loading
    ) {
      hasFetchedRef.current = true
      setFetchLoading(true)
      setFetchError(null)
      getChargerDiscovery(geo.lat, geo.lng)
        .then((response) => {
          setFetchedChargers(response.chargers)
          setFetchLoading(false)
        })
        .catch((err) => {
          console.error('[PreChargingScreen] Failed to fetch chargers:', err)
          console.error('[PreChargingScreen] API URL:', `${import.meta.env.VITE_API_BASE_URL || 'https://api.nerava.network'}/v1/chargers/discovery`)
          console.error('[PreChargingScreen] Location:', { lat: geo.lat, lng: geo.lng })
          setFetchError(err.message)
          setFetchLoading(false)
          // Don't fall back to mock data - show error instead
        })
    }
  }, [propChargers, geo.lat, geo.lng, geo.loading])

  // Use props if provided, otherwise use fetched data
  const chargers = (propChargers && propChargers.length > 0) ? propChargers : fetchedChargers
  const loading = propLoading || fetchLoading || geo.loading
  
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
      <header className="bg-white px-5 h-[60px] flex-shrink-0 flex items-center justify-between border-b border-[#E4E6EB] relative">
        {/* Left spacer for balance */}
        <div className="w-8"></div>
        
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
            ) : fetchError ? (
              <div className="text-center text-red-500 py-8">Error: {fetchError}</div>
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
