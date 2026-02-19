import { Button } from '../shared/Button'
import { modalBackdropOpacity } from '../../ui/tokens'

interface ExclusiveActivatedModalProps {
  merchantName: string
  perkTitle: string
  remainingMinutes: number
  onStartWalking: () => void
  onViewDetails: () => void
}

export function ExclusiveActivatedModal({
  merchantName: _merchantName,
  perkTitle: _perkTitle,
  remainingMinutes,
  onStartWalking,
  onViewDetails,
}: ExclusiveActivatedModalProps) {
  // Note: merchantName and perkTitle available for future enhancement
  void _merchantName
  void _perkTitle
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 backdrop-blur-sm"
        style={{ backgroundColor: `rgba(0, 0, 0, ${modalBackdropOpacity})` }}
      />

      {/* Modal */}
      <div
        className="relative bg-white rounded-[20px] shadow-modal max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Wallet icon */}
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
              />
            </svg>
          </div>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-3">
          Exclusive Activated
        </h2>

        {/* Status badges */}
        <div className="flex flex-col items-center gap-2 mb-6">
          <span className="inline-block px-4 py-1.5 rounded-full bg-gray-100 text-gray-700 text-sm font-medium">
            Active while you're charging
          </span>
          <span className="inline-block px-4 py-1.5 rounded-full bg-gray-100 text-gray-700 text-sm font-medium">
            {remainingMinutes} minutes remaining
          </span>
        </div>

        {/* Buttons */}
        <div className="space-y-3">
          <Button
            variant="primary"
            className="w-full"
            onClick={onStartWalking}
          >
            Start Walking
          </Button>
          <Button
            variant="secondary"
            className="w-full border-0 bg-transparent hover:bg-gray-50"
            onClick={onViewDetails}
          >
            View Details
          </Button>
        </div>
      </div>
    </div>
  )
}
