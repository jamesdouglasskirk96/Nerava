/**
 * Exclusive Active Screen - shown after activating an exclusive offer
 * Displays countdown timer and visit verification button
 */
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Heart, Share2, Navigation, MapPin } from 'lucide-react'
import { useGeolocation } from '../../hooks/useGeolocation'
import { useMerchantDetails } from '../../services/api'
import { resolvePhotoUrl } from '../../services/api'
import { Button } from '../shared/Button'

interface ExclusiveActiveScreenProps {
  expiresAt?: Date  // When the exclusive expires
  merchantId?: string
}

export function ExclusiveActiveScreen() {
  const { merchantId } = useParams<{ merchantId: string }>()
  const navigate = useNavigate()
  const geo = useGeolocation(5000) // Poll every 5 seconds

  const { data: merchantData, isLoading } = useMerchantDetails(merchantId || null)

  // Countdown state - 60 minutes from now by default
  const [expiresAt] = useState(() => {
    // Check if there's stored expiration time
    const stored = sessionStorage.getItem(`exclusive_expires_${merchantId}`)
    if (stored) {
      return new Date(stored)
    }
    // Default to 60 minutes from now
    const expires = new Date(Date.now() + 60 * 60 * 1000)
    sessionStorage.setItem(`exclusive_expires_${merchantId}`, expires.toISOString())
    return expires
  })

  const [timeRemaining, setTimeRemaining] = useState('')
  const [isExpired, setIsExpired] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [visitVerified, setVisitVerified] = useState(false)

  // Update countdown every second
  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date()
      const diff = expiresAt.getTime() - now.getTime()

      if (diff <= 0) {
        setIsExpired(true)
        setTimeRemaining('Expired')
        return
      }

      const minutes = Math.floor(diff / 60000)
      const seconds = Math.floor((diff % 60000) / 1000)
      setTimeRemaining(`${minutes} minute${minutes !== 1 ? 's' : ''} remaining`)
    }

    updateCountdown()
    const interval = setInterval(updateCountdown, 1000)
    return () => clearInterval(interval)
  }, [expiresAt])

  const handleGetDirections = () => {
    if (merchantData?.actions.get_directions_url) {
      window.open(merchantData.actions.get_directions_url, '_blank')
    }
  }

  const handleVerifyVisit = async () => {
    if (!geo.isNearMerchant) {
      alert(`You must be within 40m of the merchant to verify your visit. Current distance: ${Math.round(geo.distanceToMerchant || 0)}m`)
      return
    }

    setIsVerifying(true)
    try {
      // TODO: Call API to verify visit
      // For now, just mark as verified
      await new Promise(resolve => setTimeout(resolve, 1000))
      setVisitVerified(true)
      alert('Visit verified! Show this screen to the merchant to redeem your offer.')
    } catch (error) {
      alert('Failed to verify visit')
    } finally {
      setIsVerifying(false)
    }
  }

  if (isLoading || !merchantData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <p className="text-gray-600">Loading...</p>
      </div>
    )
  }

  const photoUrl = resolvePhotoUrl(
    (merchantData.merchant as any).photo_urls?.[0] || merchantData.merchant.photo_url
  )

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Hero Image */}
      <div className="relative h-48 bg-gray-200">
        {photoUrl && (
          <img
            src={photoUrl}
            alt={merchantData.merchant.name}
            className="w-full h-full object-cover"
          />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />

        {/* Exclusive Active Badge - top left */}
        <div className="absolute top-4 left-4">
          <div className="px-3 py-1.5 bg-green-500 rounded-full shadow-lg">
            <span className="text-sm text-white font-medium">Exclusive Active</span>
          </div>
        </div>

        {/* Heart and Share - top right */}
        <div className="absolute top-4 right-4 flex items-center gap-2">
          <button className="w-10 h-10 bg-[#1877F2] rounded-full flex items-center justify-center shadow-lg">
            <Heart className="w-5 h-5 text-white fill-white" />
          </button>
          <button className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg">
            <Share2 className="w-5 h-5 text-gray-700" />
          </button>
        </div>

        {/* Countdown Badge - bottom center */}
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
          <div className={`px-4 py-2 rounded-full shadow-lg ${isExpired ? 'bg-red-500' : 'bg-white'}`}>
            <span className={`text-sm font-medium ${isExpired ? 'text-white' : 'text-gray-800'}`}>
              {timeRemaining}
            </span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 px-6 py-5">
        {/* Merchant Name */}
        <h1 className="text-2xl font-bold text-gray-900">{merchantData.merchant.name}</h1>
        <p className="text-sm text-gray-500 mt-0.5">{merchantData.merchant.category}</p>

        {/* Instruction Banner */}
        <div className="mt-4 p-3 bg-blue-50 rounded-xl border border-blue-100">
          <p className="text-sm text-blue-800 text-center">
            Walk to {merchantData.merchant.name} and show this screen
          </p>
        </div>

        {/* Exclusive Offer Card */}
        {merchantData.perk && (
          <div className="mt-4 bg-gradient-to-r from-yellow-500/10 to-amber-500/10 rounded-2xl p-4 border border-yellow-600/20">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 bg-yellow-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-lg">🎁</span>
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-sm mb-0.5 text-yellow-900">Exclusive Offer</h3>
                <p className="text-sm text-yellow-800">{merchantData.perk.title}</p>
                <p className="text-xs text-yellow-700 mt-1">{merchantData.perk.description}</p>
              </div>
            </div>
          </div>
        )}

        {/* Distance Info */}
        <div className="mt-4 bg-gray-50 rounded-xl p-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-blue-100 rounded-full flex items-center justify-center">
              <MapPin className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h3 className="font-medium text-sm">Distance</h3>
              <p className="text-xs text-gray-500">
                {merchantData.moment.distance_miles} miles · {merchantData.moment.label}
              </p>
            </div>
          </div>
        </div>

        {/* Hours */}
        {(merchantData.merchant as any).hours_today && (
          <div className="mt-3 bg-gray-50 rounded-xl p-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-sm">🕐</span>
              </div>
              <div>
                <h3 className="font-medium text-sm">Hours Today</h3>
                <p className="text-xs text-gray-500">{(merchantData.merchant as any).hours_today}</p>
              </div>
            </div>
          </div>
        )}

        {/* Location Status */}
        <div className="mt-4 p-3 bg-gray-100 rounded-lg">
          <p className="text-xs text-gray-600 text-center">
            {geo.loading ? 'Getting location...' : geo.error ? (
              <span className="text-red-600">Location error: {geo.error}</span>
            ) : geo.distanceToMerchant === null ? (
              <span className="text-orange-600">Unable to determine location. Enable GPS or set mock location in console.</span>
            ) : (
              <>
                Distance to merchant: {Math.round(geo.distanceToMerchant)}m
                {geo.isNearMerchant ? (
                  <span className="text-green-600 font-medium"> (Within range)</span>
                ) : (
                  <span className="text-orange-600"> (Need to be within 40m)</span>
                )}
              </>
            )}
          </p>
        </div>
      </div>

      {/* Bottom Buttons */}
      <div className="px-6 pb-8 space-y-3">
        <Button
          variant="secondary"
          onClick={handleGetDirections}
          className="w-full flex items-center justify-center gap-2"
        >
          <Navigation className="w-4 h-4" />
          Get Directions
        </Button>

        {visitVerified ? (
          <div className="w-full py-3 bg-green-500 rounded-full text-center">
            <span className="text-white font-medium">Visit Verified ✓</span>
          </div>
        ) : (
          <Button
            variant="primary"
            onClick={handleVerifyVisit}
            disabled={!geo.isNearMerchant || isVerifying || isExpired}
            className="w-full"
          >
            {isVerifying ? 'Verifying...' : isExpired ? 'Offer Expired' : "I'm at the Merchant"}
          </Button>
        )}

        {!geo.isNearMerchant && !visitVerified && !isExpired && (
          <p className="text-xs text-center text-gray-500">
            You must be within 40m of the merchant to verify your visit
          </p>
        )}
      </div>
    </div>
  )
}
