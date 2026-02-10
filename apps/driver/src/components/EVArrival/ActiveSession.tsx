import { useState, useEffect } from 'react'
import { capture } from '../../analytics'
import { DRIVER_EVENTS } from '../../analytics/events'

interface QueuedOrder {
  id: string
  status: 'QUEUED' | 'RELEASED' | 'CANCELED' | 'EXPIRED'
  ordering_url: string
  release_url?: string | null
  order_number?: string | null
  created_at: string
  released_at?: string | null
}

interface ActiveSessionProps {
  sessionId: string
  merchantName: string
  arrivalType: string
  orderNumber?: string | null
  orderSource?: string | null
  orderTotalCents?: number | null
  expiresAt: string
  status: string
  merchantNotifiedAt?: string | null
  orderingUrl?: string | null
  vehicleColor?: string | null
  vehicleModel?: string | null
  onBindOrder: (orderNumber: string, estimatedTotalCents?: number) => void
  onCancel: () => void
  isBindingOrder?: boolean
  queuedOrder?: QueuedOrder | null
  onQueueOrder?: () => Promise<void>
  isQueueingOrder?: boolean
}

export function ActiveSession({
  sessionId,
  merchantName,
  arrivalType,
  orderNumber,
  orderSource,
  orderTotalCents,
  expiresAt,
  status,
  merchantNotifiedAt,
  orderingUrl,
  vehicleColor,
  vehicleModel,
  onBindOrder,
  onCancel,
  isBindingOrder,
  queuedOrder,
  onQueueOrder,
  isQueueingOrder,
}: ActiveSessionProps) {
  const [inputOrderNumber, setInputOrderNumber] = useState('')
  const [estimateCents, setEstimateCents] = useState('')
  const [timeLeft, setTimeLeft] = useState('')
  const [showManualEntry, setShowManualEntry] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => {
      const diff = new Date(expiresAt).getTime() - Date.now()
      if (diff <= 0) {
        setTimeLeft('Expired')
        clearInterval(timer)
        return
      }
      const h = Math.floor(diff / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      setTimeLeft(h > 0 ? `${h}h ${m}m` : `${m}m`)
    }, 1000)
    return () => clearInterval(timer)
  }, [expiresAt])

  const handleSubmitOrder = () => {
    if (!inputOrderNumber.trim()) return
    const est = estimateCents ? Math.round(parseFloat(estimateCents) * 100) : undefined
    capture(DRIVER_EVENTS.EV_ARRIVAL_ORDER_BOUND, {
      session_id: sessionId,
      order_number: inputOrderNumber,
    })
    onBindOrder(inputOrderNumber.trim(), est)
  }

  const modeLabel = arrivalType === 'ev_curbside' ? 'EV Curbside' : 'EV Dine-In'

  const statusDisplay = () => {
    if (merchantNotifiedAt) {
      return (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <p className="text-green-800 font-medium">On-site confirmed</p>
          <p className="text-green-600 text-sm">{merchantName} has been notified</p>
        </div>
      )
    }
    if (status === 'arrived') {
      return (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-blue-800 font-medium">Merchant notified</p>
          <p className="text-blue-600 text-sm">Your order details have been sent</p>
        </div>
      )
    }
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
        <p className="text-amber-800 font-medium">Waiting for arrival at charger</p>
        <p className="text-amber-600 text-sm">We'll notify {merchantName} when you arrive</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-5 mx-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-bold text-gray-900">EV Arrival Active</h2>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
          {modeLabel}
        </span>
      </div>

      <p className="text-gray-600 mb-4">{merchantName}</p>

      {/* Vehicle info */}
      {vehicleColor && vehicleModel && (
        <p className="text-sm text-gray-500 mb-3">
          🚗 {vehicleColor} {vehicleModel}
        </p>
      )}

      {/* Status */}
      <div className="mb-4">{statusDisplay()}</div>

      {/* Check-In While You Charge - Queued Order Flow */}
      {orderingUrl && !orderNumber && !queuedOrder && (
        <div className="mb-4">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4">
            <p className="text-sm font-semibold text-gray-800 mb-2">
              Check-In While You Charge
            </p>
            <p className="text-xs text-gray-600 mb-3">
              Order now and {merchantName} will start preparing when you arrive at the charger.
            </p>
            <button
              onClick={async () => {
                capture(DRIVER_EVENTS.EV_ARRIVAL_ORDER_LINK_CLICKED, {
                  session_id: sessionId,
                  merchant_name: merchantName,
                })
                if (onQueueOrder) {
                  await onQueueOrder()
                }
                window.open(orderingUrl, '_blank')
              }}
              disabled={isQueueingOrder}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isQueueingOrder ? (
                'Setting up...'
              ) : (
                <>
                  <span>🍽️</span> Order from {merchantName}
                </>
              )}
            </button>
          </div>

          <button
            onClick={() => setShowManualEntry(true)}
            className="w-full mt-2 text-sm text-gray-500 hover:text-gray-700"
          >
            I already ordered — enter order #
          </button>
        </div>
      )}

      {/* Queued Order Status */}
      {queuedOrder && queuedOrder.status === 'QUEUED' && (
        <div className="mb-4">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">⏳</span>
              <p className="text-sm font-semibold text-amber-800">Order Queued</p>
            </div>
            <p className="text-xs text-amber-700">
              Your order will be sent to {merchantName} when you arrive at the charger.
            </p>
            {queuedOrder.order_number && (
              <p className="text-xs text-amber-600 mt-1">Order #{queuedOrder.order_number}</p>
            )}
          </div>
        </div>
      )}

      {/* Released Order - Food is being prepared */}
      {queuedOrder && queuedOrder.status === 'RELEASED' && (
        <div className="mb-4">
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">🎉</span>
              <p className="text-sm font-semibold text-green-800">Order Released!</p>
            </div>
            <p className="text-xs text-green-700 mb-2">
              {merchantName} is preparing your order now.
            </p>
            {queuedOrder.release_url && (
              <a
                href={queuedOrder.release_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-green-600 underline"
              >
                View your order
              </a>
            )}
          </div>
        </div>
      )}

      {/* Manual Order Entry (fallback) */}
      {(showManualEntry || (!orderingUrl && !orderNumber)) && !queuedOrder && (
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Enter your order number</p>
          <input
            type="text"
            value={inputOrderNumber}
            onChange={e => setInputOrderNumber(e.target.value)}
            placeholder="Order #"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-2 text-gray-900"
          />
          <input
            type="number"
            value={estimateCents}
            onChange={e => setEstimateCents(e.target.value)}
            placeholder="Estimated total (optional, e.g. 25.00)"
            step="0.01"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-3 text-gray-900 text-sm"
          />
          <button
            onClick={handleSubmitOrder}
            disabled={!inputOrderNumber.trim() || isBindingOrder}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium disabled:opacity-50"
          >
            {isBindingOrder ? 'Saving...' : 'Save Order #'}
          </button>
          {orderingUrl && (
            <button
              onClick={() => setShowManualEntry(false)}
              className="w-full mt-2 text-sm text-gray-500 hover:text-gray-700"
            >
              Back
            </button>
          )}
        </div>
      )}

      {/* Order info display */}
      {orderNumber && (
        <div className="bg-gray-50 rounded-lg p-3 mb-4">
          <p className="text-sm text-gray-900 font-medium">Order #{orderNumber}</p>
          {orderTotalCents && (
            <p className="text-sm text-gray-600">
              ${(orderTotalCents / 100).toFixed(2)}
              {orderSource && orderSource !== 'manual' && (
                <span className="text-green-600 ml-1">({orderSource} verified)</span>
              )}
            </p>
          )}
        </div>
      )}

      {/* Timer and cancel */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
        <span className="text-sm text-gray-500">
          Expires in {timeLeft}
        </span>
        <button
          onClick={() => {
            capture(DRIVER_EVENTS.EV_ARRIVAL_CANCELED, { session_id: sessionId })
            onCancel()
          }}
          className="text-sm text-red-500 hover:text-red-600"
        >
          Cancel arrival
        </button>
      </div>
    </div>
  )
}
