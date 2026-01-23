import { useState, useMemo } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { usePartyCluster } from '../../services/api'
import { MerchantCarousel } from '../MerchantCarousel/MerchantCarousel'
import type { MerchantCard } from '../../types'

// Number of merchants per page (1 featured + 2 nearby)
const MERCHANTS_PER_PAGE = 3

// Convert MerchantCard to Merchant format for MerchantCarousel
function convertMerchantCardToMerchant(card: MerchantCard, isFeatured: boolean): any {
  // Derive walkTime from distance_to_charger
  let walkTime = '3 min walk'
  if (card.distance_to_charger) {
    const distanceMiles = card.distance_to_charger / 1609.34 // Convert meters to miles
    if (distanceMiles < 0.2) {
      walkTime = '3 min walk'
    } else if (distanceMiles < 0.3) {
      walkTime = '5 min walk'
    } else {
      walkTime = '8 min walk'
    }
  }

  // Hero image selection: prefer photo_urls[0] for outdoor patio images, fallback to photo_url
  // TODO: If API provides photo ordering/filtering metadata, use that to prefer outdoor patio images
  const heroImageUrl = card.photo_urls?.[0] || card.photo_url || ''

  // Determine badge text - support multiple badge types (walk time vs contextual)
  // TODO: API doesn't currently provide contextual badge text (e.g., "On your way out")
  // For now, derive from distance_to_charger. If API adds contextual badge field, use that instead.
  let badgeText = walkTime
  // Future: if card has contextual_badge field, use that: badgeText = card.contextual_badge || walkTime

  return {
    id: card.id,
    name: card.name,
    // For primary merchant: use category from merchant data, not Google Places description
    // For secondary: use description as category fallback
    category: card.is_primary ? (card.offer_preview ? 'Restaurant' : card.description || 'Restaurant') : (card.description || 'Restaurant'),
    walkTime: badgeText, // Use badgeText to support multiple badge types
    imageUrl: heroImageUrl,
    badge: card.is_primary ? '⭐ Exclusive' : undefined,
    isFeatured,
    is_primary: card.is_primary, // Pass through for Exclusive badge check
    distance: card.distance_to_charger ? `${(card.distance_to_charger / 1609.34).toFixed(1)} miles` : undefined,
    hoursStatus: undefined, // Could be added if open_now is available
    description: card.description,
    exclusiveOffer: card.offer_preview?.description,
    // Pass photo_urls array and photo_url for secondary cards to ensure proper image selection
    photo_urls: card.photo_urls || [],
    photo_url: card.photo_url, // Preserve photo_url for fallback
  }
}

export function PartyClusterScreen() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const clusterId = searchParams.get('cluster_id')
  const [currentSetIndex, setCurrentSetIndex] = useState(0)

  const { data: clusterData, isLoading, error } = usePartyCluster(clusterId)

  const handleMerchantClick = (merchant: any) => {
    // Pass charger_id for exclusive activation flow
    const chargerId = clusterData?.cluster_id ? 'canyon_ridge_supercharger' : ''
    navigate(`/app/merchant/${merchant.id}?charger_id=${chargerId}`)
  }

  const handleToggleLike = (merchantId: string) => {
    // Load liked merchants from localStorage
    const storedLikes = localStorage.getItem('neravaLikes')
    const likedMerchants = storedLikes ? new Set(JSON.parse(storedLikes) as string[]) : new Set()

    // Toggle like
    if (likedMerchants.has(merchantId)) {
      likedMerchants.delete(merchantId)
    } else {
      likedMerchants.add(merchantId)
    }

    // Save back to localStorage
    localStorage.setItem('neravaLikes', JSON.stringify(Array.from(likedMerchants)))
  }

  // Calculate merchant sets for pagination (up to 12 merchants = 4 pages of 3)
  const { merchantSets, totalSets } = useMemo(() => {
    if (!clusterData) return { merchantSets: [], totalSets: 0 }

    // Get all merchants, primary first
    const allMerchants = [
      clusterData.primary_merchant,
      ...clusterData.merchants.filter(m => !m.is_primary)
    ].slice(0, 12) // Limit to 12 merchants max

    // Group into sets of 3 (1 featured + 2 nearby per page)
    const sets: Array<{ featured: any; nearby: any[] }> = []

    for (let i = 0; i < allMerchants.length; i += MERCHANTS_PER_PAGE) {
      const pageItems = allMerchants.slice(i, i + MERCHANTS_PER_PAGE)
      if (pageItems.length > 0) {
        sets.push({
          featured: convertMerchantCardToMerchant(pageItems[0], true),
          nearby: pageItems.slice(1).map(m => convertMerchantCardToMerchant(m, false))
        })
      }
    }

    return { merchantSets: sets, totalSets: sets.length }
  }, [clusterData])

  const handlePrevSet = () => {
    setCurrentSetIndex(prev => (prev > 0 ? prev - 1 : totalSets - 1))
  }

  const handleNextSet = () => {
    setCurrentSetIndex(prev => (prev < totalSets - 1 ? prev + 1 : 0))
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white text-[#050505] max-w-md mx-auto flex items-center justify-center">
        <p className="text-[#65676B]">Loading party cluster...</p>
      </div>
    )
  }

  if (error || !clusterData) {
    const errorMessage = error instanceof Error 
      ? error.message 
      : error 
        ? String(error) 
        : 'Unknown error'
    
    // Check if it's a network/CORS error
    const isNetworkError = errorMessage.includes('Failed to fetch') || 
                           errorMessage.includes('network_error') ||
                           errorMessage.includes('NetworkError')
    
    return (
      <div className="min-h-screen bg-white text-[#050505] max-w-md mx-auto flex items-center justify-center">
        <div className="text-center px-6">
          <p className="text-red-600 font-semibold">Error loading party cluster</p>
          <p className="text-sm text-[#65676B] mt-2">{errorMessage}</p>
          {isNetworkError && (
            <div className="mt-4 text-xs text-[#65676B] space-y-1">
              <p>Possible causes:</p>
              <p>• Backend not running on http://localhost:8001</p>
              <p>• CORS blocking the request</p>
              <p>• Check browser console for details</p>
              <p className="mt-2">API URL: {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'}</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Get the current merchant set based on pagination
  const currentMerchantSet = merchantSets[currentSetIndex] || { featured: null, nearby: [] }

  // Load liked merchants from localStorage
  const storedLikes = localStorage.getItem('neravaLikes')
  const likedMerchants = storedLikes ? new Set(JSON.parse(storedLikes) as string[]) : new Set()

  // Don't render if no merchant set
  if (!currentMerchantSet.featured) {
    return (
      <div className="min-h-screen bg-white text-[#050505] max-w-md mx-auto flex items-center justify-center">
        <p className="text-[#65676B]">No merchants available</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white text-[#050505] max-w-md mx-auto flex flex-col h-screen overflow-hidden">
      {/* Status Header */}
      <header className="bg-white border-b border-[#E4E6EB] flex-shrink-0">
        <div className="flex items-center justify-between px-5 py-3">
          <div className="flex items-center">
            <img
              src="/nerava-logo.png"
              alt="Nerava"
              className="h-6 w-auto"
            />
          </div>
          <div className="px-3 py-1.5 bg-[#1877F2] rounded-full">
            <span className="text-xs text-white font-medium">Charging Active</span>
          </div>
        </div>
      </header>

      {/* Moment Header */}
      <div className="text-center px-6 pt-4 pb-1 flex-shrink-0">
        <h1 className="text-2xl sm:text-3xl mb-1 whitespace-nowrap">What to do while you charge</h1>
        <p className="text-sm text-[#65676B] whitespace-nowrap">Curated access, active while charging</p>
      </div>

      {/* Merchant Carousel */}
      <div className="flex-1 overflow-hidden">
        <MerchantCarousel
          merchantSet={currentMerchantSet}
          isCharging={true}
          onPrevSet={handlePrevSet}
          onNextSet={handleNextSet}
          currentSetIndex={currentSetIndex}
          totalSets={totalSets}
          onMerchantClick={handleMerchantClick}
          likedMerchants={likedMerchants}
        />
      </div>
    </div>
  )
}

