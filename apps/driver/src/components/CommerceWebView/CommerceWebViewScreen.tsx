/**
 * CommerceWebViewScreen
 *
 * Modal WebView screen for in-app ordering from merchant POS systems.
 * Shows Nerava header bar above an iframe with the merchant's ordering page.
 * Handles auto-detection of order confirmation and manual "I completed my order" fallback.
 */
import { useState, useRef, useCallback, useEffect } from 'react'
import { X, Zap, Gift, Clock, CheckCircle } from 'lucide-react'
import { getAdapter } from '../../services/posAdapters'
import type { MerchantOrderingConfig } from '../../services/posAdapters'
import { capture, DRIVER_EVENTS } from '../../analytics'

export interface CommerceWebViewProps {
  merchantName: string
  merchantId: string
  merchantConfig: MerchantOrderingConfig
  sessionId: string
  chargerId: string
  chargeTimeRemainingMin?: number
  chargePercentage?: number
  timeSincePlugInMin?: number
  userPhone?: string
  onClose: () => void
  onOrderCompleted: (completionMethod: 'auto_url' | 'manual_button') => void
}

export function CommerceWebViewScreen({
  merchantName,
  merchantId,
  merchantConfig,
  sessionId,
  chargerId,
  chargeTimeRemainingMin,
  chargePercentage,
  timeSincePlugInMin,
  userPhone,
  onClose,
  onOrderCompleted,
}: CommerceWebViewProps) {
  const [orderCompleted, setOrderCompleted] = useState(false)
  const [showSuccessModal, setShowSuccessModal] = useState(false)
  const [completionMethod, setCompletionMethod] = useState<'auto_url' | 'manual_button'>('auto_url')
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const openedAtRef = useRef(Date.now())
  const hasInjectedRef = useRef(false)

  const posType = merchantConfig.pos_type || 'other'
  const adapter = getAdapter(posType)

  // Build ordering URL
  const orderingUrl = merchantConfig.ordering_url
    ? adapter.buildOrderingURL(
        merchantConfig.ordering_url,
        sessionId,
        userPhone,
        merchantConfig.nerava_discount_code || undefined,
      )
    : null

  // Fire webview opened event
  useEffect(() => {
    capture(DRIVER_EVENTS.ORDERING_WEBVIEW_OPENED, {
      session_id: sessionId,
      merchant_id: merchantId,
      pos_type: posType,
      charger_id: chargerId,
      charge_pct_at_open: chargePercentage,
      time_since_plug_in_minutes: timeSincePlugInMin,
      discount_code_generated: !!merchantConfig.nerava_discount_code,
    })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Inject phone/discount after iframe loads
  const handleIframeLoad = useCallback(() => {
    if (hasInjectedRef.current || !iframeRef.current) return
    hasInjectedRef.current = true

    try {
      const iframe = iframeRef.current
      if (userPhone) {
        const phoneJS = adapter.getPhoneInjectJS(userPhone, merchantConfig.phone_field_selector || undefined)
        if (phoneJS) {
          iframe.contentWindow?.postMessage({ type: 'nerava_inject', script: phoneJS }, '*')
        }
      }
      if (merchantConfig.nerava_discount_code) {
        const discountJS = adapter.getDiscountInjectJS(
          merchantConfig.nerava_discount_code,
          merchantConfig.discount_param_key || undefined,
        )
        if (discountJS) {
          iframe.contentWindow?.postMessage({ type: 'nerava_inject', script: discountJS }, '*')
        }
      }
    } catch {
      // Cross-origin — injection may not work, that's OK
    }
  }, [adapter, userPhone, merchantConfig])

  // Listen for URL changes via message events (for cross-origin iframes)
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'nerava_url_change' && event.data.url) {
        checkConfirmation(event.data.url)
      }
    }
    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const checkConfirmation = useCallback((url: string) => {
    if (orderCompleted) return
    const confirmed = adapter.detectOrderConfirmation(url, merchantConfig.confirmation_url_pattern || undefined)
    if (confirmed) {
      handleOrderComplete('auto_url')
    }
  }, [orderCompleted, adapter, merchantConfig])

  const handleOrderComplete = useCallback((method: 'auto_url' | 'manual_button') => {
    if (orderCompleted) return
    setOrderCompleted(true)
    setCompletionMethod(method)
    setShowSuccessModal(true)

    const timeInWebviewSeconds = Math.round((Date.now() - openedAtRef.current) / 1000)
    capture(DRIVER_EVENTS.ORDER_COMPLETED, {
      session_id: sessionId,
      merchant_id: merchantId,
      pos_type: posType,
      discount_code_redeemed: !!merchantConfig.nerava_discount_code,
      reward_applied: !!merchantConfig.nerava_offer,
      time_to_order_minutes: Math.round(timeInWebviewSeconds / 60),
      completion_method: method,
    })
  }, [orderCompleted, sessionId, merchantId, posType, merchantConfig])

  const handleClose = useCallback(() => {
    if (!orderCompleted) {
      const timeInWebviewSeconds = Math.round((Date.now() - openedAtRef.current) / 1000)
      capture(DRIVER_EVENTS.ORDERING_WEBVIEW_CLOSED_WITHOUT_ORDER, {
        session_id: sessionId,
        merchant_id: merchantId,
        pos_type: posType,
        time_in_webview_seconds: timeInWebviewSeconds,
      })
    }
    onClose()
  }, [orderCompleted, sessionId, merchantId, posType, onClose])

  const handleSuccessDone = useCallback(() => {
    setShowSuccessModal(false)
    onOrderCompleted(completionMethod)
  }, [completionMethod, onOrderCompleted])

  if (!orderingUrl) {
    return null
  }

  return (
    <>
      {/* Full-screen modal overlay */}
      <div className="fixed inset-0 z-[4000] bg-white flex flex-col">
        {/* Nerava Header Bar */}
        <div className="flex-shrink-0 bg-white border-b border-gray-100 px-4 pt-2 pb-3" style={{ paddingTop: 'calc(env(safe-area-inset-top, 0px) + 0.5rem)' }}>
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <p className="text-base font-semibold text-[#050505] truncate">{merchantName}</p>
              <div className="flex items-center gap-2 mt-1 flex-wrap">
                {/* Charging verified badge */}
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-50 border border-green-200 rounded-full text-xs font-medium text-green-700">
                  <Zap className="w-3 h-3" />
                  Charging verified
                </span>

                {/* Charge time remaining */}
                {chargeTimeRemainingMin != null && chargeTimeRemainingMin > 0 && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-50 border border-gray-200 rounded-full text-xs text-[#65676B]">
                    <Clock className="w-3 h-3" />
                    {chargeTimeRemainingMin} min left
                  </span>
                )}

                {/* Offer badge */}
                {merchantConfig.nerava_offer && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-50 border border-amber-200 rounded-full text-xs font-medium text-amber-700">
                    <Gift className="w-3 h-3" />
                    {merchantConfig.nerava_offer}
                  </span>
                )}
              </div>
            </div>

            <button
              onClick={handleClose}
              className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 ml-3 flex-shrink-0"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </div>
        </div>

        {/* WebView (iframe) */}
        <div className="flex-1 relative">
          <iframe
            ref={iframeRef}
            src={orderingUrl}
            className="w-full h-full border-0"
            onLoad={handleIframeLoad}
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-top-navigation"
            title={`Order from ${merchantName}`}
          />

          {/* Manual confirmation button for "other" POS */}
          {posType === 'other' && !orderCompleted && (
            <div className="absolute bottom-6 inset-x-4" style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}>
              <button
                onClick={() => handleOrderComplete('manual_button')}
                className="w-full py-4 bg-green-600 text-white text-base font-semibold rounded-2xl shadow-lg active:scale-[0.98] transition-transform flex items-center justify-center gap-2"
              >
                <CheckCircle className="w-5 h-5" />
                I completed my order
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Success Modal (Part 3: Order Completion Flow) */}
      {showSuccessModal && (
        <OrderSuccessModal
          merchantName={merchantName}
          nerava_offer={merchantConfig.nerava_offer}
          chargeTimeRemainingMin={chargeTimeRemainingMin}
          onDone={handleSuccessDone}
        />
      )}
    </>
  )
}

// ─── Order Success Modal ────────────────────────────────────────────────────

function OrderSuccessModal({
  merchantName,
  nerava_offer,
  chargeTimeRemainingMin,
  onDone,
}: {
  merchantName: string
  nerava_offer?: string | null
  chargeTimeRemainingMin?: number
  onDone: () => void
}) {
  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-[4100]" />
      <div className="fixed inset-x-4 top-1/2 -translate-y-1/2 z-[4101] bg-white rounded-3xl p-6 max-w-md mx-auto shadow-xl">
        {/* Green checkmark */}
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="w-9 h-9 text-green-600" />
        </div>

        <h3 className="text-lg font-semibold text-[#050505] text-center mb-2">
          Order placed at {merchantName}
        </h3>

        {nerava_offer && (
          <p className="text-sm text-green-700 text-center mb-3">
            Your {nerava_offer} has been applied
          </p>
        )}

        {chargeTimeRemainingMin != null && chargeTimeRemainingMin > 0 && (
          <div className="bg-gray-50 rounded-xl p-3 mb-4 text-center">
            <p className="text-xs text-[#65676B]">Estimated pickup</p>
            <p className="text-sm font-medium text-[#050505]">
              ~{chargeTimeRemainingMin} min (when your charge completes)
            </p>
          </div>
        )}

        <button
          onClick={onDone}
          className="w-full py-3 bg-[#1877F2] text-white text-sm font-semibold rounded-xl active:scale-[0.98] transition-transform"
        >
          Done
        </button>
      </div>
    </>
  )
}
