import { X, QrCode } from 'lucide-react'
import { useState } from 'react'
import type { RefuelDetails } from '../RefuelIntentModal'

interface FullScreenTicketProps {
  reservationId: string
  merchantName: string
  refuelDetails?: RefuelDetails | null
  onClose: () => void
}

/**
 * Fullscreen ticket view - signature interaction for showing reservation to host.
 * Large reservation code with shimmer animation, intent display, and copy functionality.
 */
export function FullScreenTicket({
  reservationId,
  merchantName,
  refuelDetails,
  onClose,
}: FullScreenTicketProps) {
  const [copied, setCopied] = useState(false)

  const getIntentLabel = () => {
    if (!refuelDetails) return null
    
    switch (refuelDetails.intent) {
      case 'eat':
        const getPartySizeLabel = (size: number) => {
          if (size === 2) return 'Party of 1-2'
          if (size === 4) return 'Party of 3-4'
          if (size >= 5) return 'Party of 5+'
          return `Party of ${size}`
        }
        
        return {
          primary: 'DINING',
          secondary: `(${getPartySizeLabel(refuelDetails.partySize || 2)})`
        }
      case 'work':
        return {
          primary: 'WORK SESSION',
          secondary: refuelDetails.needsPowerOutlet ? '(Power Outlet)' : ''
        }
      case 'quick-stop':
        return {
          primary: 'QUICK STOP',
          secondary: refuelDetails.isToGo ? '(To-Go)' : ''
        }
    }
  }

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(reservationId)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy code:', error)
    }
  }

  const intentLabel = getIntentLabel()

  return (
    <div className="fixed inset-0 bg-white z-[60] flex items-center justify-center">
      <div className="max-w-md w-full p-8">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 w-12 h-12 bg-[#F7F8FA] rounded-full flex items-center justify-center hover:bg-[#E4E6EB] active:scale-95 transition-all"
          aria-label="Close"
        >
          <X className="w-6 h-6 text-[#050505]" />
        </button>

        {/* Hero: The "Fast Pass" Screen */}
        <div className="text-center mb-8">
          <div className="mb-6">
            <div className="w-20 h-20 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <QrCode className="w-10 h-10 text-[#1877F2]" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Show this to your host</h1>
            <p className="text-sm text-[#65676B]">at {merchantName}</p>
          </div>

          {/* Massive Intent Display */}
          {intentLabel && (
            <div className="bg-gradient-to-r from-[#1877F2]/5 to-[#1877F2]/10 rounded-3xl p-8 mb-6 border-2 border-[#1877F2]/30">
              <p className="text-6xl font-black text-[#1877F2] tracking-tight leading-none mb-2">
                {intentLabel.primary}
              </p>
              {intentLabel.secondary && (
                <p className="text-3xl font-bold text-[#1877F2] tracking-tight mb-4">
                  {intentLabel.secondary}
                </p>
              )}
              
              {/* Animated Verification Code with shimmer */}
              <div className="bg-white rounded-2xl p-6 border-2 border-[#1877F2]/20 mt-4">
                <p className="text-xs text-[#65676B] mb-2">Reservation ID</p>
                <p className="text-2xl font-mono font-black tracking-wide text-[#050505] animate-shimmer break-all">
                  {reservationId}
                </p>
              </div>
            </div>
          )}

          {/* Fallback if no intent details */}
          {!intentLabel && (
            <div className="bg-gradient-to-r from-[#1877F2]/5 to-[#1877F2]/10 rounded-3xl p-8 mb-6 border-2 border-[#1877F2]/30">
              <div className="bg-white rounded-2xl p-6 border-2 border-[#1877F2]/20">
                <p className="text-xs text-[#65676B] mb-2">Reservation ID</p>
                <p className="text-2xl font-mono font-black tracking-wide text-[#050505] animate-shimmer break-all">
                  {reservationId}
                </p>
              </div>
            </div>
          )}

          {/* Copy Code Button */}
          <button
            onClick={handleCopyCode}
            className="w-full py-4 bg-[#F7F8FA] text-[#050505] rounded-2xl font-medium hover:bg-[#E4E6EB] active:scale-98 transition-all"
          >
            {copied ? 'Copied!' : 'Copy Code'}
          </button>
        </div>
      </div>
    </div>
  )
}
