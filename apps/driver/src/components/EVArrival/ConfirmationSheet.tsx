import { useState } from 'react'
import { capture } from '../../analytics'
import { DRIVER_EVENTS } from '../../analytics/events'
import type { ArrivalMode } from './ModeSelector'

interface ConfirmationSheetProps {
  merchantName: string
  merchantId: string
  arrivalMode: ArrivalMode
  vehicleColor?: string
  vehicleModel?: string
  onConfirm: () => void
  onCancel: () => void
  onEditVehicle: () => void
  isLoading?: boolean
}

export function ConfirmationSheet({
  merchantName,
  merchantId,
  arrivalMode,
  vehicleColor,
  vehicleModel,
  onConfirm,
  onCancel,
  onEditVehicle,
  isLoading,
}: ConfirmationSheetProps) {
  const [verifying, setVerifying] = useState(false)

  const modeLabel = arrivalMode === 'ev_curbside' ? 'EV Curbside Arrival' : 'EV Dine-In Arrival'
  const vehicleDesc = vehicleColor && vehicleModel
    ? `${vehicleColor} ${vehicleModel}`
    : 'No vehicle set'

  const handleConfirm = async () => {
    setVerifying(true)
    capture(DRIVER_EVENTS.EV_ARRIVAL_CONFIRMED, {
      merchant_id: merchantId,
      arrival_type: arrivalMode,
    })
    // Show verifying interstitial for 1 second
    await new Promise(resolve => setTimeout(resolve, 1000))
    onConfirm()
  }

  if (verifying) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
        <div className="bg-white rounded-2xl p-8 text-center max-w-sm mx-4">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-blue-50 flex items-center justify-center animate-pulse">
            <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <p className="text-lg font-semibold text-gray-900">Verifying...</p>
          <p className="text-sm text-gray-500 mt-1">Setting up your EV Arrival</p>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40">
      <div
        className="w-full max-w-md bg-white rounded-t-2xl p-6 pb-8 animate-slide-up"
        role="dialog"
        aria-label="Confirm EV Arrival"
      >
        <div className="w-12 h-1 bg-gray-300 rounded-full mx-auto mb-6" />

        <h2 className="text-xl font-bold text-gray-900 mb-1">{modeLabel}</h2>
        <p className="text-gray-600 mb-4">at {merchantName}</p>

        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🚗</span>
            <div>
              <p className="font-medium text-gray-900">{vehicleDesc}</p>
              <button
                onClick={onEditVehicle}
                className="text-blue-600 text-sm hover:underline"
              >
                Edit vehicle
              </button>
            </div>
          </div>
        </div>

        <p className="text-sm text-gray-500 mb-6">
          When you arrive at the charger, we'll notify {merchantName} to have your order ready.
        </p>

        <button
          onClick={handleConfirm}
          disabled={isLoading}
          className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold disabled:opacity-50"
        >
          {isLoading ? 'Creating...' : 'Confirm EV Arrival'}
        </button>

        <button
          onClick={onCancel}
          className="w-full mt-3 text-gray-500 text-sm py-2"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
