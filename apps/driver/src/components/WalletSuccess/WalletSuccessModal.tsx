import { Button } from '../shared/Button'
import { modalBackdropOpacity } from '../../ui/tokens'

interface WalletSuccessModalProps {
  merchantName: string
  perkTitle: string
  activeCopy?: string
  onClose: () => void
  onViewWallet?: () => void
}

export function WalletSuccessModal({
  merchantName,
  perkTitle,
  activeCopy,
  onClose,
  onViewWallet,
}: WalletSuccessModalProps) {
  const handleViewWallet = () => {
    if (onViewWallet) {
      onViewWallet()
    } else {
      // Default: show stub wallet preview or close
      alert('Wallet pass preview - Coming soon')
      onClose()
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop - 60% opacity matching Figma */}
      <div
        className="absolute inset-0 backdrop-blur-sm"
        style={{ backgroundColor: `rgba(0, 0, 0, ${modalBackdropOpacity})` }}
      />

      {/* Modal - Border radius 20px matching Figma */}
      <div
        className="relative bg-white rounded-[20px] shadow-modal max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Success icon - 64x64px matching Figma */}
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={3}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
        </div>

        {/* Title - "Exclusive Activated" - 24px Bold, center-aligned */}
        <h2 className="text-2xl font-bold text-[#050505] text-center mb-2">
          Exclusive Activated
        </h2>

        {/* Subtitle - Active copy text - 16px Regular, center-aligned */}
        <p className="text-base font-normal leading-6 text-[#656A6B] text-center mb-6">
          {activeCopy || 'Active for the next 60 minutes'}
        </p>

        {/* Merchant context row - Gray background, rounded corners */}
        <div className="bg-gray-50 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-[#050505]">{merchantName}</span>
            <span className="text-xs font-medium text-[#656A6B]">{perkTitle}</span>
          </div>
        </div>

        {/* CTA - "View Wallet" - Full width, primary style */}
        <Button variant="primary" className="w-full" onClick={handleViewWallet}>
          View Wallet
        </Button>
      </div>
    </div>
  )
}

