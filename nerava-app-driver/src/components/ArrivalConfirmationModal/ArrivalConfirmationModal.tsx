// Arrival Confirmation Modal - "You're Here"
import { CheckCircle } from 'lucide-react'

interface ArrivalConfirmationModalProps {
  isOpen: boolean
  merchantName: string
  exclusiveBadge?: string
  onDone: () => void
}

/**
 * Modal shown when user arrives at merchant
 * Shows merchant name + Exclusive badge
 * CTA: "Done" → triggers completion modal
 */
export function ArrivalConfirmationModal({
  isOpen,
  merchantName,
  exclusiveBadge,
  onDone,
}: ArrivalConfirmationModalProps) {
  if (!isOpen) return null

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

        {/* Pass Card */}
        <div className="bg-[#F7F8FA] rounded-2xl p-4 mb-6 border border-[#E4E6EB]">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium mb-1">{merchantName}</h3>
              <p className="text-xs text-[#65676B]">Exclusive Active</p>
            </div>
            <div className="text-right">
              {exclusiveBadge && (
                <div className="px-2.5 py-1 bg-yellow-500/10 rounded-full border border-yellow-500/20 inline-block">
                  <span className="text-xs text-yellow-700">{exclusiveBadge}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Button */}
        <button
          onClick={onDone}
          className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
        >
          Done
        </button>
      </div>
    </div>
  )
}

