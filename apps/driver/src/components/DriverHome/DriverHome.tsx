// DriverHome - Main orchestrator component for driver app
import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
// Zap import removed - using logo image instead
import { useDriverSessionContext } from '../../contexts/DriverSessionContext'
import { useExclusiveSessionState } from '../../hooks/useExclusiveSessionState'
import { useQueryClient } from '@tanstack/react-query'
import {
  useIntentCapture,
  useActivateExclusive,
  useCompleteExclusive,
  useActiveExclusive,
  useLocationCheck,
  checkLocation,
} from '../../services/api'
import { useChargingState } from '../../hooks/useChargingState'
import { capture, page, DRIVER_EVENTS } from '../../analytics'
import { useFavorites } from '../../contexts/FavoritesContext'
import { MerchantCarousel } from '../MerchantCarousel/MerchantCarousel'
import { ExclusiveActiveView } from '../ExclusiveActiveView/ExclusiveActiveView'
import { PrimaryFilters } from '../shared/PrimaryFilters'
import { MerchantDetailModal } from '../MerchantDetail/MerchantDetailModal'
import { ActivateExclusiveModal } from '../ActivateExclusiveModal/ActivateExclusiveModal'
import { ArrivalConfirmationModal } from '../ArrivalConfirmationModal/ArrivalConfirmationModal'
import { CompletionFeedbackModal } from '../CompletionFeedbackModal/CompletionFeedbackModal'
import { PreferencesModal } from '../Preferences/PreferencesModal'
import { AnalyticsDebugPanel } from '../Debug/AnalyticsDebugPanel'
import { AccountPage } from '../Account/AccountPage'
import { WalletModal } from '../Wallet/WalletModal'
import { User, Wallet } from 'lucide-react'
import { groupMerchantsIntoSets, groupChargersIntoSets } from '../../utils/dataMapping'
import { getChargerSetsWithExperiences } from '../../mock/mockChargers'
import { isMockMode, isDemoMode } from '../../services/api'
import { getGuaranteedFallbackChargerSet, getGuaranteedFallbackCharger } from '../../utils/guaranteedFallback'
import { preloadImage } from '../../utils/imageCache'
import { ErrorBanner } from '../shared/ErrorBanner'
import { InlineError } from '../shared/InlineError'
import { MerchantCarouselSkeleton, MerchantCardSkeleton } from '../shared/Skeleton'
import { Badge } from '../shared/Badge'
import { ImageWithFallback } from '../shared/ImageWithFallback'
import { LocationDeniedScreen } from '../LocationDenied/LocationDeniedScreen'
import { StateTransitionToast } from '../shared/StateTransitionToast'
import { FEATURE_FLAGS } from '../../config/featureFlags'
import type { MockMerchant } from '../../mock/mockMerchants'
import type { MockCharger } from '../../mock/mockChargers'
import type { ExclusiveMerchant } from '../../hooks/useExclusiveSessionState'
import type { MerchantSummary } from '../../types'
import { isTeslaBrowser } from '../../utils/evBrowserDetection'
import { EVHome } from '../EVHome/EVHome'

/**
 * Main entry point that orchestrates the three states:
 * - PRE_CHARGING: User not within charger radius
 * - CHARGING_ACTIVE: User within charger radius
 * - EXCLUSIVE_ACTIVE: User has activated an exclusive
 */
export function DriverHome() {
  const {
    locationPermission,
    locationFix,
    coordinates,
    appChargingState,
    sessionId,
    setAppChargingState,
    setSessionId,
    requestLocationPermission,
  } = useDriverSessionContext()
  const { activeExclusive, remainingMinutes, activateExclusive: activateExclusiveLocal, clearExclusive } = useExclusiveSessionState()
  const activateExclusiveMutation = useActivateExclusive()
  const completeExclusiveMutation = useCompleteExclusive()
  const { data: activeExclusiveData } = useActiveExclusive()
  const queryClient = useQueryClient()
  const manualClearRef = useRef(false)
  const chargingState = useChargingState()
  const navigate = useNavigate()

  // Check if Tesla browser - if so, show EV-optimized experience
  const [isTeslaBrowserUser, setIsTeslaBrowserUser] = useState(false)
  
  useEffect(() => {
    setIsTeslaBrowserUser(isTeslaBrowser())
  }, [])

  // If Tesla browser and at charger, show EV-optimized experience
  // This can be enhanced to check if actually at charger via coordinates
  if (isTeslaBrowserUser && coordinates && appChargingState === 'CHARGING_ACTIVE') {
    return <EVHome />
  }

  const [currentSetIndex, setCurrentSetIndex] = useState(0)
  const [selectedMerchant, setSelectedMerchant] = useState<MockMerchant | null>(null)
  const [selectedCharger, setSelectedCharger] = useState<MockCharger | null>(null)
  const [showActivateModal, setShowActivateModal] = useState(false)
  const [showArrivalModal, setShowArrivalModal] = useState(false)
  const [showCompletionModal, setShowCompletionModal] = useState(false)
  const [showPreferencesModal, setShowPreferencesModal] = useState(false)
  const [checkedIn, setCheckedIn] = useState(false)
  const [checkedInMerchantName, setCheckedInMerchantName] = useState<string | null>(null)
  const { favorites: likedMerchants, toggleFavorite, isFavorite } = useFavorites()
  const [primaryFilters, setPrimaryFilters] = useState<string[]>([])
  
  // Wrapper to maintain compatibility with existing components
  const handleToggleLike = (merchantId: string) => {
    toggleFavorite(merchantId).catch((e) => {
      console.error('Failed to toggle favorite', e)
    })
  }

  // Primary filter toggle handler
  const handleFilterToggle = (filter: string) => {
    setPrimaryFilters((prev) =>
      prev.includes(filter) ? prev.filter((f) => f !== filter) : [...prev, filter]
    )
  }

  // Filter merchants by selected amenities
  // When multiple filters are selected, merchant must match ALL of them (AND logic)
  const filterMerchantsByAmenities = useCallback((merchants: MerchantSummary[]): MerchantSummary[] => {
    if (primaryFilters.length === 0) return merchants

    return merchants.filter((merchant) => {
      return primaryFilters.every((filter) => {
        const types = merchant.types || []
        const typesLower = types.map((t) => t.toLowerCase())

        switch (filter) {
          case 'bathroom':
            // Future: Check amenity votes, for now assume all merchants have bathrooms
            return true
          case 'food':
            return (
              typesLower.some((t) =>
                t.includes('restaurant') ||
                t.includes('food') ||
                t.includes('cafe') ||
                t.includes('bakery') ||
                t.includes('meal')
              ) || merchant.is_primary === true // Primary merchants are often food
            )
          case 'wifi':
            // Future: Check amenity votes, for now assume cafes/restaurants have WiFi
            return typesLower.some(
              (t) => t.includes('cafe') || t.includes('restaurant') || t.includes('coffee')
            )
          case 'pets':
            return typesLower.some((t) => t.includes('pet') || t.includes('veterinary'))
          case 'music':
            // Future: Check merchant type or amenity data
            return false // Placeholder - no backend data yet
          case 'patio':
            // Future: Check merchant type or amenity data
            return false // Placeholder - no backend data yet
          default:
            return false
        }
      })
    })
  }, [primaryFilters])
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    // Check if user has access token
    return !!localStorage.getItem('access_token')
  })
  const [inlineError, setInlineError] = useState<string | null>(null)

  // Sync authentication state when tokens change
  useEffect(() => {
    const checkAuth = () => {
      const hasToken = !!localStorage.getItem('access_token')
      setIsAuthenticated(hasToken)
    }
    
    // Check on mount and listen for storage changes
    checkAuth()
    window.addEventListener('storage', checkAuth)
    
    // Also check periodically (in case tokens are set in same window)
    const interval = setInterval(checkAuth, 1000)
    
    return () => {
      window.removeEventListener('storage', checkAuth)
      clearInterval(interval)
    }
  }, [])
  // Initialize browse mode if location is unavailable
  const [browseMode, setBrowseMode] = useState(() => {
    // Check if we should start in browse mode (no coordinates available)
    const stored = localStorage.getItem('nerava_driver_session')
    if (stored) {
      try {
        const data = JSON.parse(stored)
        if (!data.coordinates || !data.coordinates.lat || !data.coordinates.lng) {
          return true // Enable browse mode if no stored coordinates
        }
      } catch {
        // Invalid JSON, enable browse mode
        return true
      }
    }
    // Enable browse mode by default if no location available
    return true
  })
  
  // CRITICAL: Ensure app always starts in PRE_CHARGING state to show charger immediately
  // Only run on mount, before any API data loads
  const [hasInitialized, setHasInitialized] = useState(false)
  useEffect(() => {
    if (!hasInitialized && appChargingState !== 'PRE_CHARGING' && chargingState.state !== 'EXCLUSIVE_ACTIVE' && !activeExclusive) {
      setAppChargingState('PRE_CHARGING')
      chargingState.transitionTo('PRE_CHARGING')
      setHasInitialized(true)
    }
  }, [hasInitialized, appChargingState, chargingState.state, activeExclusive, setAppChargingState])
  const [showTransitionToast, setShowTransitionToast] = useState(false)
  const [showAccountPage, setShowAccountPage] = useState(false)
  const [showWalletModal, setShowWalletModal] = useState(false)

  // Active EV session state (from Tesla verify-charging)
  const [activeEVSession, setActiveEVSession] = useState<{
    code: string;
    merchant_name: string | null;
    expires_at: string;
  } | null>(null)
  const [showEVCodeOverlay, setShowEVCodeOverlay] = useState(false)

  // Wallet balance state (auth state is declared above with localStorage check)
  const [walletBalance, setWalletBalance] = useState(0)
  const [walletPending, setWalletPending] = useState(0)
  const [mockTransactions] = useState<Array<{ id: string; type: 'credit' | 'withdrawal'; description: string; amount: number; timestamp: string }>>([])

  // Fetch wallet balance when authenticated
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      const fetchWalletBalance = async () => {
        try {
          const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://api.nerava.network'
          const response = await fetch(`${API_BASE}/v1/wallet/balance`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          })
          if (response.ok) {
            const data = await response.json()
            setWalletBalance(data.available_cents || 0)
            setWalletPending(data.pending_cents || 0)
          }
        } catch (err) {
          console.error('Failed to fetch wallet balance:', err)
        }
      }
      fetchWalletBalance()
    } else {
      setWalletBalance(0)
      setWalletPending(0)
    }
  }, [isAuthenticated])
  // Fetch active EV session (Tesla verify-charging codes)
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setActiveEVSession(null)
      return
    }

    const fetchActiveEVCodes = async () => {
      try {
        const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://api.nerava.network'
        const response = await fetch(`${API_BASE}/v1/auth/tesla/codes`, {
          headers: { 'Authorization': `Bearer ${token}` },
        })
        if (response.ok) {
          const codes = await response.json()
          // Find first active, non-expired code
          // Server returns UTC datetimes without 'Z' — append it for correct parsing
          const now = new Date()
          const active = codes.find((c: any) => {
            const expiresStr = c.expires_at.endsWith('Z') ? c.expires_at : c.expires_at + 'Z'
            return c.status === 'active' && new Date(expiresStr) > now
          })
          setActiveEVSession(active || null)
        }
      } catch (err) {
        console.error('Failed to fetch EV codes:', err)
      }
    }
    fetchActiveEVCodes()

    // Refresh every 60 seconds
    const interval = setInterval(fetchActiveEVCodes, 60000)
    return () => clearInterval(interval)
  }, [isAuthenticated])

  const lastChargingStateRef = useRef(appChargingState)

  // Default center for browse mode - Canyon Ridge charger location for demo
  // This ensures Asadas Grill shows up when users open the app
  // Use useMemo to keep stable reference and avoid re-renders
  const DEFAULT_CENTER = useMemo(() => ({ lat: 30.3979, lng: -97.7044, accuracy_m: 10, last_fix_ts: Date.now() }), [])
  
  // Auto-enable browse mode when location is denied, skipped, or unknown (if no coordinates)
  useEffect(() => {
    if ((locationPermission === 'denied' || locationPermission === 'skipped') && !browseMode) {
      setBrowseMode(true)
    } else if (locationPermission === 'unknown' && !coordinates && !browseMode) {
      // Auto-enable browse mode immediately if location permission is unknown and no coordinates
      // This allows the app to show content even if user hasn't granted location yet
      setBrowseMode(true)
    }
  }, [locationPermission, browseMode, coordinates])
  
  // Use coordinates or default center in browse mode
  const effectiveCoordinates = coordinates || (browseMode ? DEFAULT_CENTER : null)

  // Intent capture request - only when location is available (or browse mode) and not in EXCLUSIVE_ACTIVE
  // Use useMemo to prevent infinite fetch loops - the request object must be stable
  // CRITICAL: Round coordinates to 4 decimal places to prevent GPS fluctuation from causing refetches
  const intentRequest = useMemo(() => {
    if (!effectiveCoordinates || chargingState.state === 'EXCLUSIVE_ACTIVE') {
      return null
    }
    // Round to 4 decimal places (~11m precision) to prevent GPS fluctuation loops
    const roundedLat = Math.round(effectiveCoordinates.lat * 10000) / 10000
    const roundedLng = Math.round(effectiveCoordinates.lng * 10000) / 10000
    return {
      lat: roundedLat,
      lng: roundedLng,
      accuracy_m: Math.round(effectiveCoordinates.accuracy_m || 0),
      client_ts: new Date().toISOString(), // This is fine now since useMemo prevents re-creation
    }
  }, [
    // Use rounded values in dependency array to prevent recalculation on GPS fluctuation
    effectiveCoordinates ? Math.round(effectiveCoordinates.lat * 10000) : null,
    effectiveCoordinates ? Math.round(effectiveCoordinates.lng * 10000) : null,
    effectiveCoordinates ? Math.round(effectiveCoordinates.accuracy_m || 0) : null,
    chargingState.state
  ])

  const { data: intentData, isLoading: intentLoading, error: intentError, refetch: refetchIntent } = useIntentCapture(intentRequest)
  
  // Capture intent capture request when coordinates become available
  useEffect(() => {
    if (intentRequest && !intentLoading && !intentData) {
      capture(DRIVER_EVENTS.INTENT_CAPTURE_REQUEST, {
        location_accuracy: coordinates?.accuracy_m,
      })
    }
  }, [intentRequest, intentLoading, intentData, coordinates])

  // Store session_id when intent capture succeeds
  useEffect(() => {
    if (intentData?.session_id && intentData.session_id !== sessionId) {
      setSessionId(intentData.session_id)
      capture(DRIVER_EVENTS.INTENT_CAPTURE_SUCCESS, {
        session_id: intentData.session_id,
        location_accuracy: coordinates?.accuracy_m,
        merchant_count: intentData.merchants?.length || 0,
      })
    }
  }, [intentData?.session_id, sessionId, setSessionId, coordinates, intentData])
  
  // Capture page view on mount
  useEffect(() => {
    page('home')
  }, [])
  
  // Capture location permission events
  useEffect(() => {
    if (locationPermission === 'granted') {
      capture(DRIVER_EVENTS.LOCATION_PERMISSION_GRANTED)
    } else if (locationPermission === 'denied') {
      capture(DRIVER_EVENTS.LOCATION_PERMISSION_DENIED)
    }
  }, [locationPermission])

  // Determine which data to use (mock or real)
  const useMockData = isMockMode()
  const useDemoData = isDemoMode()
  const mockChargerSets = getChargerSetsWithExperiences()

  // Real data from intent capture
  // Debug: Log intent data to console
  useEffect(() => {
    if (intentData) {
      console.log('[DriverHome] Intent data received:', {
        merchants_count: intentData.merchants?.length || 0,
        merchants: intentData.merchants,
        chargers_count: intentData.chargers?.length || 0,
        chargers: intentData.chargers,
        charger_summary: intentData.charger_summary,
        confidence_tier: intentData.confidence_tier,
        appChargingState,
      })
    }
  }, [intentData, appChargingState])
  
  // Check for API errors first (used in multiple places below)
  const hasApiError = intentError !== null && intentError !== undefined

  // Fix: Check for array existence AND length > 0 (empty array is truthy but has no items)
  // Apply filters before grouping into sets
  const filteredMerchants = intentData?.merchants && Array.isArray(intentData.merchants) && intentData.merchants.length > 0
    ? filterMerchantsByAmenities(intentData.merchants)
    : []
  const realMerchantSets = filteredMerchants.length > 0
    ? groupMerchantsIntoSets(filteredMerchants)
    : []
  // CRITICAL: Always create charger sets when chargers exist - this ensures chargers ALWAYS display
  // Use new chargers array if available, fall back to charger_summary for backward compatibility
  const chargersSource = intentData?.chargers && intentData.chargers.length > 0
    ? intentData.chargers
    : intentData?.charger_summary
    ? [intentData.charger_summary]
    : []
  const realChargerSets = chargersSource.length > 0
    ? groupChargersIntoSets(chargersSource, intentData?.merchants || [])
    : []

  const hasChargers = chargersSource.length > 0

  // CRITICAL: If chargers exist, ALWAYS use real charger sets (never mock or empty)
  // Even if realChargerSets is empty, we'll recreate it in finalChargerSets below
  const chargerSets = hasChargers
    ? realChargerSets  // Always use real charger sets if chargers exist, even if empty (will be recreated below)
    : useMockData || (useDemoData && hasApiError && realChargerSets.length === 0)
    ? mockChargerSets
    : realChargerSets

  // Use charger sets in PRE_CHARGING mode, merchant sets in CHARGING_ACTIVE mode
  // CRITICAL: If chargers exist but chargerSets is empty, recreate it as a fallback
  // This ensures chargers ALWAYS display when chargers exist
  const finalChargerSets = (hasChargers && chargerSets.length === 0)
    ? groupChargersIntoSets(chargersSource, intentData?.merchants || [])
    : chargerSets
  
  // CRITICAL: Only use guaranteed fallback when API returns no chargers
  // If real chargers exist, use them directly (no mock data prepended)
  const guaranteedFallbackSet = getGuaranteedFallbackChargerSet()
  const guaranteedChargerSets = finalChargerSets.length > 0
    ? finalChargerSets // Use real chargers from API
    : guaranteedFallbackSet // Only show fallback when no real chargers exist
  
  // Charger-first design: always show charger sets in the main carousel.
  // Users access merchants by tapping a charger card.
  const activeSets = guaranteedChargerSets

  // Get nearest charger for radius check (first one, since they're sorted by distance)
  const nearestCharger = chargersSource[0]

  // Debug: Log computed sets
  useEffect(() => {
    console.log('[DriverHome] Computed sets:', {
      realMerchantSets_length: realMerchantSets.length,
      realChargerSets_length: realChargerSets.length,
      chargerSets_length: chargerSets.length,
      finalChargerSets_length: finalChargerSets.length,
      guaranteedChargerSets_length: guaranteedChargerSets.length,
      activeSets_length: activeSets.length,
      appChargingState,
      useMockData,
      useDemoData,
      hasApiError,
      intentData_merchants_length: intentData?.merchants?.length || 0,
      chargers_count: chargersSource.length,
      chargers_ids: chargersSource.map(c => c.id),
      nearest_charger_id: nearestCharger?.id,
      nearest_charger_distance_m: nearestCharger?.distance_m,
      using_guaranteed_fallback: guaranteedChargerSets[0]?.featured?.id === 'canyon_ridge_tesla' && finalChargerSets.length === 0,
    })
  }, [realMerchantSets, realChargerSets, chargerSets, finalChargerSets, guaranteedChargerSets, activeSets, appChargingState, useMockData, useDemoData, hasApiError, intentData, chargersSource, nearestCharger])

  // CRITICAL: Always have a fallback set - use guaranteed fallback if nothing else available
  // Ensure currentSet always has valid data, defaulting to guaranteed fallback charger
  const currentSet = activeSets[currentSetIndex] || guaranteedChargerSets[0] || {
    featured: getGuaranteedFallbackCharger(),
    nearby: []
  }

  // Preload next carousel image when index changes
  useEffect(() => {
    if (activeSets.length > 0) {
      const nextIndex = (currentSetIndex + 1) % activeSets.length
      const nextSet = activeSets[nextIndex]
      if (nextSet?.featured?.imageUrl) {
        preloadImage(nextSet.featured.imageUrl).catch(() => {
          // Silently fail - preload is best effort
        })
      }
    }
  }, [currentSetIndex, activeSets])

  // Determine if user is in charger radius (for PRE_CHARGING state)
  const isInChargerRadius =
    appChargingState === 'CHARGING_ACTIVE' ||
    (nearestCharger && nearestCharger.distance_m < 150) ||
    (intentData?.confidence_tier === 'A')


  const handleMerchantClick = (item: MockMerchant | MockCharger) => {
    // Check if it's a charger (has experiences) or a merchant (has isSponsored/badges)
    if ('experiences' in item && item.experiences) {
      // It's a charger - show the charger detail with merchant list
      setSelectedCharger(item as MockCharger)
    } else if ('isSponsored' in item || 'badges' in item) {
      // It's a merchant - show merchant details modal
      // Track merchant click
      capture(DRIVER_EVENTS.MERCHANT_CLICKED, {
        merchant_id: item.id,
        merchant_name: item.name,
        category: item.category || 'unknown',
        source: 'home_list',
        path: window.location.pathname,
      })
      setSelectedMerchant(item as MockMerchant)
    }
  }

  const handleChargerMerchantClick = (merchantId: string, photoUrl?: string | null) => {
    // Close charger detail and navigate to merchant detail page
    setSelectedCharger(null)
    const params = new URLSearchParams()
    if (photoUrl) params.set('photo', photoUrl)
    const queryString = params.toString()
    navigate(`/m/${merchantId}${queryString ? `?${queryString}` : ''}`)
  }

  const handleExperienceClick = (experienceId: string, photoUrl?: string | null) => {
    // Navigate to merchant detail page
    const params = new URLSearchParams()
    if (photoUrl) params.set('photo', photoUrl)
    const queryString = params.toString()
    navigate(`/m/${experienceId}${queryString ? `?${queryString}` : ''}`)
  }

  const handleCloseMerchantDetails = () => {
    setSelectedMerchant(null)
  }

  const handleActivateExclusive = async (merchant: MockMerchant) => {
    // ALWAYS do real-time location check first (not relying on state which can be manually toggled)
    if (!isMockMode()) {
      if (!coordinates) {
        setInlineError('Location required to activate exclusive offers.')
        return
      }

      try {
        const locationCheckResult = await checkLocation(coordinates.lat, coordinates.lng)
        if (!locationCheckResult.in_charger_radius) {
          capture(DRIVER_EVENTS.EXCLUSIVE_ACTIVATE_BLOCKED_OUTSIDE_RADIUS, {
            merchant_id: merchant.id,
            distance_m: locationCheckResult.distance_m,
            required_radius_m: 150,
          })
          setInlineError(`You must be at the charger to activate exclusive offers. You are ${Math.round(locationCheckResult.distance_m || 0)}m away.`)
          return
        }
      } catch (error) {
        console.error('Location check failed:', error)
        setInlineError('Unable to verify your location. Please try again.')
        return
      }
    }

    // Location verified - now check authentication
    if (!isAuthenticated) {
      // Show OTP modal for phone verification
      setSelectedMerchant(merchant)
      setShowActivateModal(true)
    } else {
      // User is already authenticated, proceed directly to activation
      handleActivateExclusiveDirect(merchant)
    }
  }

  // Check location to detect charger radius (for UI state, exclusive activation, etc.)
  const locationCheck = useLocationCheck(coordinates?.lat || null, coordinates?.lng || null)

  useEffect(() => {
    if (locationCheck.data && coordinates) {
      if (locationCheck.data.in_charger_radius && chargingState.state === 'PRE_CHARGING') {
        if (lastChargingStateRef.current === 'PRE_CHARGING') {
          setShowTransitionToast(true)
        }
        chargingState.transitionTo('CHARGING_ACTIVE')
        setAppChargingState('CHARGING_ACTIVE')
        lastChargingStateRef.current = 'CHARGING_ACTIVE'
      } else if (!locationCheck.data.in_charger_radius && chargingState.state === 'CHARGING_ACTIVE' && !activeExclusive) {
        chargingState.transitionTo('PRE_CHARGING')
        setAppChargingState('PRE_CHARGING')
        lastChargingStateRef.current = 'PRE_CHARGING'
      }
    }
  }, [locationCheck.data, coordinates, chargingState.state, activeExclusive, setAppChargingState])

  useEffect(() => {
    lastChargingStateRef.current = appChargingState
  }, [appChargingState])

  // Sync active exclusive from backend
  useEffect(() => {
    if (activeExclusiveData?.exclusive_session) {
      const session = activeExclusiveData.exclusive_session
      if (!activeExclusive && !manualClearRef.current) {
        // Convert backend session to ExclusiveMerchant
        const exclusiveMerchant: ExclusiveMerchant = {
          id: session.merchant_id || '',
          name: '', // Will be populated from merchant details
          walkTime: '5 min',
          expiresAt: session.expires_at,
        }
        activateExclusiveLocal(exclusiveMerchant, session.expires_at)
        chargingState.transitionTo('EXCLUSIVE_ACTIVE')
        setAppChargingState('EXCLUSIVE_ACTIVE')
      }
    } else if (activeExclusiveData?.exclusive_session === null || activeExclusiveData?.exclusive_session === undefined) {
      // Backend confirms no active session — reset manual clear flag
      manualClearRef.current = false
      if (activeExclusive) {
        // Session expired or completed
        clearExclusive()
        chargingState.transitionTo('PRE_CHARGING')
        setAppChargingState('PRE_CHARGING')
      }
    }
  }, [activeExclusiveData, activeExclusive, activateExclusiveLocal, clearExclusive, chargingState.state, setAppChargingState])

  const handleActivateExclusiveDirect = async (merchant: MockMerchant) => {
    // Check charger radius guard
    if (!coordinates) {
      setInlineError('Location required to activate exclusive.')
      return
    }

    // Capture activation click (both original and new format)
    capture(DRIVER_EVENTS.EXCLUSIVE_ACTIVATE_CLICK, {
      merchant_id: merchant.id,
    })
    capture(DRIVER_EVENTS.EXCLUSIVE_ACTIVATE_CLICKED, {
      merchant_id: merchant.id,
      path: window.location.pathname,
    })

    if (!isMockMode()) {
      // Check location first
      try {
        const locationCheckResult = await checkLocation(coordinates.lat, coordinates.lng)
        if (!locationCheckResult.in_charger_radius) {
          capture(DRIVER_EVENTS.EXCLUSIVE_ACTIVATE_BLOCKED_OUTSIDE_RADIUS, {
            merchant_id: merchant.id,
            distance_m: locationCheckResult.distance_m,
            required_radius_m: 150,
          })
          setInlineError(`You must be at the charger to activate. Distance: ${locationCheckResult.distance_m?.toFixed(0)}m, required: 150m`)
          return
        }

        // Check confidence tier (from intent data)
        const confidenceTier = intentData?.confidence_tier
        if (confidenceTier && !['A', 'B'].includes(confidenceTier)) {
          setInlineError('Exclusive activation requires high confidence location. Please wait for better GPS signal.')
          return
        }

        // Activate exclusive via backend
        try {
          const response = await activateExclusiveMutation.mutateAsync({
            merchant_id: merchant.id,
            charger_id: locationCheckResult.nearest_charger_id || 'unknown',
            lat: coordinates.lat,
            lng: coordinates.lng,
            accuracy_m: coordinates.accuracy_m,
            intent_session_id: sessionId || undefined,
          })

          // Convert MockMerchant to ExclusiveMerchant
          const exclusiveMerchant: ExclusiveMerchant = {
            id: merchant.id,
            name: merchant.name,
            category: merchant.category,
            walkTime: merchant.walkTime,
            imageUrl: merchant.imageUrl,
            badge: merchant.badges?.includes('Exclusive') ? '⭐ Exclusive' : undefined,
            distance: merchant.distance,
            hours: merchant.hours,
            hoursStatus: merchant.hoursStatus,
            description: merchant.description,
            exclusiveOffer: merchant.exclusiveOffer,
          }

          activateExclusiveLocal(exclusiveMerchant, response.exclusive_session.expires_at)
          chargingState.transitionTo('EXCLUSIVE_ACTIVE')
          setAppChargingState('EXCLUSIVE_ACTIVE')
          
          capture(DRIVER_EVENTS.EXCLUSIVE_ACTIVATE_SUCCESS, {
            merchant_id: merchant.id,
            exclusive_id: response.exclusive_session.id,
            session_id: response.exclusive_session.id,
          })
        } catch (error: any) {
          console.error('Failed to activate exclusive:', error)
          capture(DRIVER_EVENTS.EXCLUSIVE_ACTIVATE_FAIL, {
            merchant_id: merchant.id,
            error: error.message || 'Unknown error',
          })
          if (error.status === 403) {
            setInlineError(error.message || 'You must be at the charger to activate exclusive.')
          } else {
            setInlineError('Failed to activate exclusive. Please try again.')
          }
          return
        }
      } catch (error) {
        console.error('Location check failed:', error)
        setInlineError('Failed to verify location. Please try again.')
        return
      }
    } else {
      // Mock mode - use local activation
      const exclusiveMerchant: ExclusiveMerchant = {
        id: merchant.id,
        name: merchant.name,
        category: merchant.category,
        walkTime: merchant.walkTime,
        imageUrl: merchant.imageUrl,
        badge: merchant.badges?.includes('Exclusive') ? '⭐ Exclusive' : undefined,
        distance: merchant.distance,
        hours: merchant.hours,
        hoursStatus: merchant.hoursStatus,
        description: merchant.description,
        exclusiveOffer: merchant.exclusiveOffer,
      }
      activateExclusiveLocal(exclusiveMerchant)
      chargingState.transitionTo('EXCLUSIVE_ACTIVE')
      setAppChargingState('EXCLUSIVE_ACTIVE')
    }

    setShowActivateModal(false)
    setSelectedMerchant(null)
  }

  const handleOTPSuccess = () => {
    // User successfully authenticated (tokens stored in auth.ts)
    setIsAuthenticated(true)
    setShowActivateModal(false)

    // DO NOT automatically activate - user is now authenticated
    // They can tap "Activate Exclusive" again which will do location check
    // This keeps OTP verification separate from location-gated activation
  }

  const handleOTPClose = () => {
    setShowActivateModal(false)
  }

  const handleArrived = () => {
    setShowArrivalModal(true)
  }

  const handleArrivalDone = async () => {
    setShowArrivalModal(false)

    // Complete the exclusive session via backend
    if (activeExclusive && !isMockMode()) {
      const activeSessionId = activeExclusiveData?.exclusive_session?.id
      if (activeSessionId) {
        try {
          await completeExclusiveMutation.mutateAsync({
            exclusive_session_id: activeSessionId,
          })
          capture(DRIVER_EVENTS.EXCLUSIVE_COMPLETE_SUCCESS, {
            merchant_id: activeExclusive.id,
            session_id: activeSessionId,
          })
        } catch (error: any) {
          console.error('Failed to complete exclusive:', error)
        }
      }
    }

    // Save merchant name for banner, then clear exclusive and return to discovery
    setCheckedInMerchantName(activeExclusive?.name || null)
    setCheckedIn(true)
    // Prevent sync logic from recreating the exclusive from stale cache
    manualClearRef.current = true
    clearExclusive()
    chargingState.transitionTo('PRE_CHARGING')
    setAppChargingState('PRE_CHARGING')
    // Invalidate cache so next fetch gets fresh data from backend
    queryClient.invalidateQueries({ queryKey: ['active-exclusive'] })

    // Auto-hide the banner after 5 seconds
    setTimeout(() => {
      setCheckedIn(false)
      setCheckedInMerchantName(null)
    }, 5000)
  }

  const handleCancelExclusive = async () => {
    // Complete/cancel the exclusive session via backend
    if (activeExclusive && !isMockMode()) {
      const activeSessionId = activeExclusiveData?.exclusive_session?.id
      if (activeSessionId) {
        try {
          await completeExclusiveMutation.mutateAsync({
            exclusive_session_id: activeSessionId,
          })
        } catch (error: any) {
          console.error('Failed to cancel exclusive:', error)
        }
      }
    }
    // Prevent sync logic from recreating the exclusive from stale cache
    manualClearRef.current = true
    clearExclusive()
    chargingState.transitionTo('PRE_CHARGING')
    setAppChargingState('PRE_CHARGING')
    // Invalidate cache so next fetch gets fresh data from backend
    queryClient.invalidateQueries({ queryKey: ['active-exclusive'] })
  }

  const handleCompletionContinue = async () => {
    setShowCompletionModal(false)
    
    // Capture completion click (both original and new format)
    if (activeExclusive) {
      capture(DRIVER_EVENTS.EXCLUSIVE_COMPLETE_CLICK, {
        merchant_id: activeExclusive.id,
      })
      capture(DRIVER_EVENTS.EXCLUSIVE_DONE_CLICKED, {
        merchant_id: activeExclusive.id,
        path: window.location.pathname,
      })
    }
    
    // Complete exclusive session via backend
    if (activeExclusive && !isMockMode()) {
      const activeSessionId = activeExclusiveData?.exclusive_session?.id
      if (activeSessionId) {
        try {
          await completeExclusiveMutation.mutateAsync({
            exclusive_session_id: activeSessionId,
          })
          
          capture(DRIVER_EVENTS.EXCLUSIVE_COMPLETE_SUCCESS, {
            merchant_id: activeExclusive.id,
            session_id: activeSessionId,
          })
        } catch (error: any) {
          console.error('Failed to complete exclusive:', error)
          capture(DRIVER_EVENTS.EXCLUSIVE_COMPLETE_FAIL, {
            merchant_id: activeExclusive.id,
            error: error.message || 'Unknown error',
          })
          // Continue anyway - show preferences
        }
      }
    }
    
    // Transition to COMPLETE state and show preferences
    chargingState.transitionTo('COMPLETE')
    setShowPreferencesModal(true)
  }

  const handlePreferencesDone = () => {
    setShowPreferencesModal(false)
    // Reset state and return to discovery
    clearExclusive()
    chargingState.transitionTo(appChargingState === 'CHARGING_ACTIVE' ? 'CHARGING_ACTIVE' : 'PRE_CHARGING')
    setAppChargingState(appChargingState === 'CHARGING_ACTIVE' ? 'CHARGING_ACTIVE' : 'PRE_CHARGING')
  }

  const handlePrevSet = () => {
    setCurrentSetIndex((prev) => (prev === 0 ? activeSets.length - 1 : prev - 1))
  }

  const handleNextSet = () => {
    setCurrentSetIndex((prev) => (prev === activeSets.length - 1 ? 0 : prev + 1))
  }

  const handleToggleCharging = () => {
    if (chargingState.state === 'PRE_CHARGING') {
      chargingState.transitionTo('CHARGING_ACTIVE')
      setAppChargingState('CHARGING_ACTIVE')
    } else if (chargingState.state === 'CHARGING_ACTIVE') {
      chargingState.transitionTo('PRE_CHARGING')
      setAppChargingState('PRE_CHARGING')
    }
    setCurrentSetIndex(0)
    setSelectedMerchant(null)
    // Reset exclusive state when switching modes
    if (activeExclusive) {
      clearExclusive()
    }
  }

  // State-based headline - removed subtitle per Figma design
  const headline = FEATURE_FLAGS.LIVE_COORDINATION_UI_V1
    ? (chargingState.state === 'PRE_CHARGING'
        ? `${guaranteedChargerSets.length} charger${guaranteedChargerSets.length !== 1 ? 's' : ''} with open stalls near you`
        : chargingState.state === 'CHARGING_ACTIVE' || chargingState.state === 'EXCLUSIVE_ACTIVE'
        ? 'Lock in your spot while you charge'
        : 'Chargers near experiences')
    : 'What to do while you charge'

  // Dev console logging
  useEffect(() => {
    console.group('Nerava Integration')
    console.log('Mock mode:', isMockMode())
    console.log('API base URL:', import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001')
    console.log('Location permission:', locationPermission)
    console.log('Location fix:', locationFix)
    console.log('Coordinates:', coordinates)
    console.log('Browse mode:', browseMode)
    console.log('Effective coordinates:', effectiveCoordinates)
    console.log('Intent request:', intentRequest)
    console.log('App charging state:', appChargingState)
    console.log('Charging state machine:', chargingState.state)
    console.log('Session ID:', sessionId)
    console.log('Intent capture loading:', intentLoading)
    console.log('Intent data:', intentData)
    console.log('Intent error:', intentError)
    console.groupEnd()
  }, [locationPermission, locationFix, coordinates, browseMode, effectiveCoordinates, intentRequest, appChargingState, sessionId, intentLoading, intentData, intentError])

  // Show location denied screen if location is denied or error (and not skipped/browse mode)
  const showLocationDenied = (locationPermission === 'denied' || locationFix === 'error') && !browseMode && locationPermission !== 'skipped'

  const handleTryAgain = () => {
    requestLocationPermission()
  }

  const handleBrowseChargers = () => {
    setBrowseMode(true)
  }

  // If location denied and not in browse mode, show recovery screen
  if (showLocationDenied) {
    return (
      <LocationDeniedScreen
        onTryAgain={handleTryAgain}
        onBrowseChargers={handleBrowseChargers}
      />
    )
  }

  // If exclusive is active, show exclusive view (ignore other states)
  if (activeExclusive && (activeExclusive || chargingState.state === 'EXCLUSIVE_ACTIVE')) {
    return (
      <>
        <ExclusiveActiveView
          merchant={activeExclusive}
          remainingMinutes={remainingMinutes}
          onArrived={handleArrived}
          onCancel={handleCancelExclusive}
          onExpired={() => {
            clearExclusive()
            chargingState.transitionTo('CHARGING_ACTIVE')
            setAppChargingState('CHARGING_ACTIVE')
          }}
          onToggleLike={handleToggleLike}
          onShare={() => {
            // Share functionality
            const url = `https://nerava.com/merchant/${activeExclusive.id}`
            navigator.clipboard.writeText(url)
          }}
          isLiked={isFavorite(activeExclusive.id)}
        />
        <ArrivalConfirmationModal
          isOpen={showArrivalModal}
          merchantName={activeExclusive.name}
          merchantId={activeExclusive.id}
          exclusiveBadge={activeExclusive.badge}
          exclusiveSessionId={activeExclusiveData?.exclusive_session?.id}
          lat={effectiveCoordinates?.lat}
          lng={effectiveCoordinates?.lng}
          onDone={handleArrivalDone}
        />
        <CompletionFeedbackModal
          isOpen={showCompletionModal}
          onContinue={handleCompletionContinue}
        />
        <PreferencesModal
          isOpen={showPreferencesModal}
          onClose={handlePreferencesDone}
        />
      </>
    )
  }

  // Discovery View - Hidden when exclusive is active
  return (
    <>
      <StateTransitionToast
        show={showTransitionToast}
        onHide={() => setShowTransitionToast(false)}
      />
      <div className="bg-white text-[#050505] max-w-md mx-auto flex flex-col overflow-hidden transition-opacity duration-300" style={{ height: 'var(--app-height, 100dvh)', minHeight: 'var(--app-height, 100dvh)' }}>
        {/* Check-in success banner */}
        {checkedIn && checkedInMerchantName && (
          <div className="bg-green-50 border-b border-green-200 px-4 py-3 flex items-center gap-3 flex-shrink-0">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-white" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-green-800">Checked in at {checkedInMerchantName}</p>
              <p className="text-xs text-green-600">Session completed successfully</p>
            </div>
            <button
              onClick={() => { setCheckedIn(false); setCheckedInMerchantName(null) }}
              className="text-green-500 hover:text-green-700 p-1"
              aria-label="Dismiss"
            >
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
            </button>
          </div>
        )}
        {/* Active EV Session Banner */}
        {activeEVSession && (
          <button
            onClick={() => setShowEVCodeOverlay(true)}
            className="w-full bg-[#1877F2] text-white px-4 py-3 flex items-center justify-between flex-shrink-0"
          >
            <div className="flex items-center gap-2">
              <span className="text-lg">⚡</span>
              <span className="font-medium text-sm">
                {activeEVSession.merchant_name || 'Active Session'}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-medium">
                {(() => {
                  // Server returns UTC without 'Z' suffix — append it for correct parsing
                  const expiresStr = activeEVSession.expires_at.endsWith('Z')
                    ? activeEVSession.expires_at
                    : activeEVSession.expires_at + 'Z'
                  const mins = Math.max(0, Math.round((new Date(expiresStr).getTime() - Date.now()) / 60000))
                  return `${mins} min left`
                })()}
              </span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </button>
        )}

        {/* Status Header */}
        <header className="bg-white border-b border-[#E4E6EB] flex-shrink-0">
          <div className="flex items-center justify-between px-5 py-3">
            <div className="flex items-center gap-1.5">
              <img 
                src="/nerava-logo.png" 
                alt="Nerava" 
                className="h-6 w-auto"
              />
              {/* Only show badges in dev/demo mode */}
              {useDemoData && (
                <Badge variant="default" className="ml-2">
                  Demo Mode
                </Badge>
              )}
              {/* Hide browse mode badge - it's an internal state, not user-facing */}
            </div>
            <div className="flex items-center gap-2">
              {/* Wallet balance button - only show when logged in */}
              {isAuthenticated && (
                <button
                  onClick={() => setShowWalletModal(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 hover:bg-gray-100 rounded-full transition-all border border-[#E4E6EB]"
                  aria-label="Wallet"
                >
                  <Wallet className="w-4 h-4 text-[#1877F2]" aria-hidden="true" />
                  <span className="text-sm font-medium text-[#050505]">${(walletBalance / 100).toFixed(2)}</span>
                </button>
              )}
              {/* Account button - always visible */}
              <button
                onClick={() => setShowAccountPage(true)}
                className="p-2 hover:bg-gray-100 rounded-full transition-all"
                aria-label="Account"
              >
                <User className="w-5 h-5 text-[#050505]" aria-hidden="true" />
              </button>
              {/* State indicator - only show in demo/dev mode, otherwise state is automatic */}
              {(useDemoData || useMockData) && (
                <button
                  onClick={handleToggleCharging}
                  className="px-3 py-1.5 bg-[#1877F2] rounded-full hover:bg-[#166FE5] active:scale-95 transition-all flex items-center justify-center"
                >
                  <span className="text-xs text-white leading-none">
                    {chargingState.state === 'CHARGING_ACTIVE' || chargingState.state === 'EXCLUSIVE_ACTIVE' ? 'Charging Active' : 'Pre-Charging'}
                  </span>
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Moment Header */}
        <div className="text-center px-6 pt-4 pb-2 flex-shrink-0">
          <h1 className="text-2xl sm:text-3xl whitespace-nowrap">{headline}</h1>
        </div>

        {/* Primary Filters - Show for PRE_CHARGING and CHARGING_ACTIVE states */}
        {(appChargingState === 'PRE_CHARGING' || appChargingState === 'CHARGING_ACTIVE') && (
          <PrimaryFilters
            selectedFilters={primaryFilters}
            onFilterToggle={handleFilterToggle}
          />
        )}

        {/* Merchant Carousel */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {/* Show error banner if API failed and not in demo mode */}
          {hasApiError && !useDemoData && !useMockData && (
            <ErrorBanner
              message="We couldn't load chargers right now. Retry."
              onRetry={() => refetchIntent()}
              isLoading={intentLoading}
            />
          )}

          {/* Inline error for activation/location failures */}
          <InlineError
            message={inlineError}
            onDismiss={() => setInlineError(null)}
            className="mx-4 mb-2"
          />

          {intentLoading && !useMockData && locationFix === 'locating' ? (
            <MerchantCarouselSkeleton />
          ) : intentLoading && !useMockData ? (
            <div className="grid gap-4 px-5">
              {[...Array(3)].map((_, i) => <MerchantCardSkeleton key={i} />)}
            </div>
          ) : activeSets.length > 0 ? (
            <MerchantCarousel
              merchantSet={currentSet}
              isCharging={chargingState.state === 'CHARGING_ACTIVE' || chargingState.state === 'EXCLUSIVE_ACTIVE'}
              onPrevSet={handlePrevSet}
              onNextSet={handleNextSet}
              currentSetIndex={currentSetIndex}
              totalSets={activeSets.length}
              onMerchantClick={handleMerchantClick}
              onExperienceClick={(id, photoUrl) => handleExperienceClick(id, photoUrl)}
              likedMerchants={likedMerchants}
            />
          ) : (
            <div className="flex flex-col items-center justify-center py-12 px-6 h-full">
              <div className="w-20 h-20 bg-[#F7F8FA] rounded-full flex items-center justify-center mb-4">
                <svg className="w-10 h-10 text-[#656A6B]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-[#050505] mb-1">No spots found</h3>
              <p className="text-sm text-[#656A6B] text-center mb-4">
                {intentLoading 
                  ? 'Loading nearby spots...'
                  : 'Try adjusting your filters or check back soon for new spots.'}
              </p>
              {!intentLoading && (
                <button
                  onClick={() => refetchIntent()}
                  className="px-6 py-2.5 bg-[#1877F2] text-white text-sm font-medium rounded-full hover:bg-[#166FE5] active:scale-[0.98] transition-all"
                >
                  Refresh
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Charger Detail Modal - Shows merchants for selected charger */}
      {selectedCharger && (
        <div className="fixed inset-0 z-50 bg-white flex flex-col" style={{ height: 'var(--app-height, 100dvh)' }}>
          {/* Header */}
          <header className="bg-white border-b border-[#E4E6EB] flex-shrink-0 px-4 py-3 flex items-center justify-between">
            <button
              onClick={() => setSelectedCharger(null)}
              className="p-2 -ml-2 hover:bg-gray-100 rounded-full"
              aria-label="Back to chargers"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div className="flex-1 text-center">
              <img src="/nerava-logo.png" alt="Nerava" className="h-6 mx-auto" />
            </div>
            <button
              onClick={() => setShowAccountPage(true)}
              className="p-2 -mr-2 hover:bg-gray-100 rounded-full"
            >
              <User className="w-5 h-5" />
            </button>
          </header>

          {/* Moment Header */}
          <div className="text-center px-6 pt-4 pb-2 flex-shrink-0">
            <h1 className="text-2xl font-medium mb-1">What to do while you charge</h1>
            <p className="text-sm text-[#65676B]">Curated access, active while charging</p>
          </div>

          {/* Content - scrollable area for merchant cards */}
          <div className="flex-1 overflow-y-auto px-5">
            {selectedCharger.experiences && selectedCharger.experiences.length > 0 ? (
              selectedCharger.experiences.map((exp, index) => (
                <div
                  key={exp.id}
                  onClick={() => handleChargerMerchantClick(exp.id, exp.imageUrl)}
                  className={`bg-[#F7F8FA] rounded-2xl shadow-md border border-[#E4E6EB] overflow-hidden cursor-pointer active:scale-[0.98] transition-transform ${index > 0 ? 'mt-4' : ''}`}
                >
                  {/* Merchant Image - Large hero */}
                  <div className="relative h-64 overflow-hidden">
                    <ImageWithFallback
                      src={exp.imageUrl}
                      alt={exp.name}
                      category={exp.category || 'restaurant'}
                      className="w-full h-full"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />
                    <div className="absolute bottom-3 left-3">
                      <span className="px-3 py-1.5 bg-[#1877F2] rounded-full text-xs font-medium text-white">
                        {exp.walkTime || '2 min walk'}
                      </span>
                    </div>
                    {exp.badge && (
                      <div className="absolute bottom-3 right-3">
                        <span className="px-3 py-1.5 bg-gradient-to-r from-yellow-500/15 to-amber-500/15 border border-yellow-600/30 rounded-full text-xs font-medium text-yellow-700">
                          {exp.badge}
                        </span>
                      </div>
                    )}
                  </div>
                  {/* Merchant Info */}
                  <div className="p-5">
                    <h3 className="text-2xl mb-1">{exp.name}</h3>
                    <p className="text-sm text-[#65676B] mb-2">{exp.category}</p>
                    <p className="text-sm text-[#1877F2] font-medium">Tap to see your free perk →</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-[#65676B]">
                {FEATURE_FLAGS.LIVE_COORDINATION_UI_V1 ? 'No live experiences at this charger.' : 'No experiences available at this charger'}
              </div>
            )}
          </div>

          {/* Bottom Navigation */}
          <div className="bg-white pt-4 px-5 border-t border-[#E4E6EB] flex-shrink-0" style={{ paddingBottom: 'calc(1.5rem + env(safe-area-inset-bottom, 0px))' }}>
            <div className="max-w-md mx-auto">
              <div className="flex items-center justify-between">
                <button
                  onClick={() => setSelectedCharger(null)}
                  className="p-3 rounded-full bg-[#F7F8FA] border border-[#E4E6EB] hover:bg-[#E4E6EB] active:scale-95 transition-all"
                  aria-label="Back to chargers"
                >
                  <svg className="w-6 h-6 text-[#050505]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <div className="flex flex-col items-center gap-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-2 rounded-full bg-[#1877F2]" />
                  </div>
                  <p className="text-xs text-[#65676B]">
                    {FEATURE_FLAGS.LIVE_COORDINATION_UI_V1 ? 'Live experiences' : 'Nearby experiences'}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedCharger(null)}
                  className="p-3 rounded-full bg-[#F7F8FA] border border-[#E4E6EB] hover:bg-[#E4E6EB] active:scale-95 transition-all"
                  aria-label="Back to chargers"
                >
                  <svg className="w-6 h-6 text-[#050505]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Merchant Details Modal */}
      {selectedMerchant && (
        <MerchantDetailModal
          merchant={selectedMerchant}
          isCharging={chargingState.state === 'CHARGING_ACTIVE' || chargingState.state === 'EXCLUSIVE_ACTIVE'}
          isInChargerRadius={isInChargerRadius}
          onClose={handleCloseMerchantDetails}
          onToggleLike={handleToggleLike}
          onActivateExclusive={handleActivateExclusive}
          likedMerchants={likedMerchants}
        />
      )}

      {/* Activation Modal (OTP) */}
      <ActivateExclusiveModal
        isOpen={showActivateModal}
        onClose={handleOTPClose}
        onSuccess={handleOTPSuccess}
      />

      {/* Preferences Modal */}
      <PreferencesModal
        isOpen={showPreferencesModal}
        onClose={handlePreferencesDone}
      />

      {/* Account Page */}
      {showAccountPage && <AccountPage onClose={() => setShowAccountPage(false)} />}

      {/* Wallet Modal */}
      <WalletModal
        isOpen={showWalletModal}
        onClose={() => setShowWalletModal(false)}
        balance={walletBalance}
        pendingBalance={walletPending}
        activeSessions={[]}
        recentTransactions={mockTransactions}
        onWithdraw={() => {
          // Would open Stripe Express onboarding
          console.log('Open Stripe Express payout')
        }}
      />

      {/* Active EV Code Overlay */}
      {showEVCodeOverlay && activeEVSession && (
        <div className="fixed inset-0 z-50 bg-white flex flex-col" style={{ height: 'var(--app-height, 100dvh)' }}>
          <header className="bg-white border-b border-[#E4E6EB] flex-shrink-0 px-4 py-3 flex items-center">
            <button
              onClick={() => setShowEVCodeOverlay(false)}
              className="flex items-center text-gray-600"
            >
              <svg className="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back
            </button>
          </header>

          <div className="flex-1 flex flex-col items-center justify-center p-6">
            <div className="w-full max-w-sm">
              <div className="p-6 bg-gradient-to-b from-green-50 to-white rounded-xl border border-green-200">
                <div className="text-center">
                  <div className="text-5xl mb-4">⚡</div>
                  <h2 className="text-xl font-bold text-gray-900 mb-2">Charging Verified!</h2>
                  <p className="text-gray-600 mb-2">
                    {activeEVSession.merchant_name || 'Active Session'}
                  </p>
                  <p className="text-sm text-gray-500 mb-6">
                    {(() => {
                      const expiresStr = activeEVSession.expires_at.endsWith('Z')
                        ? activeEVSession.expires_at
                        : activeEVSession.expires_at + 'Z'
                      const mins = Math.max(0, Math.round((new Date(expiresStr).getTime() - Date.now()) / 60000))
                      return `${mins} minutes remaining`
                    })()}
                  </p>

                  <div className="bg-white rounded-2xl border-2 border-blue-500 p-6 mb-6">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Your EV Code</p>
                    <p className="text-4xl font-mono font-bold text-blue-600 tracking-wider">
                      {activeEVSession.code}
                    </p>
                  </div>

                  <p className="text-sm text-gray-500">
                    Show this code to the merchant to redeem your reward
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Analytics Debug Panel (dev only) */}
      <AnalyticsDebugPanel />
    </>
  )
}

