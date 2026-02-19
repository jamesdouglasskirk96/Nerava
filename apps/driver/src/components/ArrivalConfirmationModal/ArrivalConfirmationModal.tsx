// Arrival Confirmation Modal - "You're Here" with Verification Code
import { useState, useEffect } from 'react'
import { CheckCircle, Loader2 } from 'lucide-react'
import { FEATURE_FLAGS } from '../../config/featureFlags'
import { capture, DRIVER_EVENTS } from '../../analytics'
import { verifyVisit, type VerifyVisitResponse } from '../../services/api'

interface ArrivalConfirmationModalProps {
  isOpen: boolean
  merchantName: string
  merchantId?: string
  exclusiveBadge?: string
  exclusiveSessionId?: string // Required for verification
  lat?: number
  lng?: number
  onDone: () => void
}

/**
 * Modal shown when user arrives at merchant
 * Shows merchant name + Exclusive badge + Verification Code
 * Verification code is generated server-side for merchant linkage
 * CTA: "Done" → triggers completion modal
 */
export function ArrivalConfirmationModal({
  isOpen,
  merchantName,
  merchantId,
  exclusiveBadge,
  exclusiveSessionId,
  lat,
  lng,
  onDone,
}: ArrivalConfirmationModalProps) {
  const [verificationData, setVerificationData] = useState<VerifyVisitResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Call verify endpoint when modal opens
  useEffect(() => {
    if (isOpen && exclusiveSessionId && !verificationData) {
      setIsLoading(true)
      setError(null)

      verifyVisit({
        exclusive_session_id: exclusiveSessionId,
        lat,
        lng,
      })
        .then((response) => {
          setVerificationData(response)
          // Track verification success
          capture(DRIVER_EVENTS.ARRIVAL_VERIFIED, {
            merchant_id: merchantId,
            merchant_name: merchantName,
            verification_code: response.verification_code,
            visit_number: response.visit_number,
            path: window.location.pathname,
          })
        })
        .catch((err) => {
          console.error('[ArrivalConfirmation] Verification failed:', err)
          setError('Unable to generate verification code')
          // Track verification failure
          capture(DRIVER_EVENTS.ARRIVAL_VERIFY_FAILED, {
            merchant_id: merchantId,
            merchant_name: merchantName,
            error: err?.message || 'unknown',
            path: window.location.pathname,
          })
        })
        .finally(() => {
          setIsLoading(false)
        })
    }
  }, [isOpen, exclusiveSessionId, merchantId, merchantName, lat, lng, verificationData])

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setVerificationData(null)
      setError(null)
      setIsLoading(false)
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleDone = () => {
    // Track arrival done click
    capture(DRIVER_EVENTS.ARRIVAL_DONE_CLICKED, {
      merchant_id: merchantId,
      merchant_name: merchantName,
      verification_code: verificationData?.verification_code,
      path: window.location.pathname,
    })
    onDone()
  }

  return (
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
          Show this screen to staff at {merchantName}
        </p>

        {/* Verification Code Card */}
        <div className="bg-gradient-to-br from-[#F0F4FF] to-[#E8F0FE] rounded-2xl p-5 mb-4 border border-[#D4E2FC]">
          <p className="text-xs text-center text-[#65676B] mb-2">Verification Code</p>
          {isLoading ? (
            <div className="flex items-center justify-center py-2">
              <Loader2 className="w-6 h-6 text-[#1877F2] animate-spin" />
            </div>
          ) : error ? (
            <p className="text-center text-red-500 text-sm">{error}</p>
          ) : verificationData ? (
            <p className="text-2xl font-bold text-center text-[#1877F2] tracking-wider">
              {verificationData.verification_code}
            </p>
          ) : (
            <p className="text-center text-[#65676B]">—</p>
          )}
        </div>

        {/* Pass Card */}
        <div className="bg-[#F7F8FA] rounded-2xl p-4 mb-6 border border-[#E4E6EB]">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium mb-1">{merchantName}</h3>
              <p className="text-xs text-[#65676B]">
                {FEATURE_FLAGS.LIVE_COORDINATION_UI_V1 ? 'Active Session' : 'Exclusive Active'}
              </p>
            </div>
            <div className="text-right">
              {exclusiveBadge && (
                <div className="px-2.5 py-1 bg-yellow-500/10 rounded-full border border-yellow-500/20 inline-flex items-center gap-1">
                  <span className="text-yellow-600">⭐</span>
                  <span className="text-xs text-yellow-700">{exclusiveBadge}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Button */}
        <button
          onClick={handleDone}
          className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
        >
          Done
        </button>
      </div>
    </div>
  )
}
