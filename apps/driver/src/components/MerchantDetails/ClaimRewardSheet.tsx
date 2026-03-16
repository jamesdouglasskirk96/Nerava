import { useState } from 'react'
import { X, Gift, Clock } from 'lucide-react'
import { Button } from '../shared/Button'

interface ClaimRewardSheetProps {
  isOpen: boolean
  merchantName: string
  rewardDescription: string
  onClose: () => void
  onClaim: () => Promise<void>
}

export function ClaimRewardSheet({
  isOpen,
  merchantName,
  rewardDescription,
  onClose,
  onClaim,
}: ClaimRewardSheetProps) {
  const [claiming, setClaiming] = useState(false)

  if (!isOpen) return null

  const handleClaim = async () => {
    setClaiming(true)
    try {
      await onClaim()
    } catch (err) {
      console.error('Failed to claim reward:', err)
    } finally {
      setClaiming(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40">
      <div className="w-full max-w-lg bg-white rounded-t-3xl p-6 pb-8 animate-slide-up">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-xl font-semibold text-[#050505]">Claim Reward</h3>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="text-center py-4">
          <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Gift className="w-8 h-8 text-amber-600" />
          </div>
          <p className="text-lg font-semibold text-[#050505] mb-1">{rewardDescription}</p>
          <p className="text-sm text-[#65676B] mb-1">at {merchantName}</p>

          <div className="flex items-center justify-center gap-1.5 text-sm text-[#65676B] mt-4 mb-6">
            <Clock className="w-4 h-4" />
            <span>You'll have 2 hours to visit and upload your receipt</span>
          </div>

          <Button
            variant="primary"
            className="w-full"
            onClick={handleClaim}
            disabled={claiming}
          >
            {claiming ? 'Claiming...' : 'Claim Reward'}
          </Button>

          <p className="text-xs text-[#65676B] mt-3">
            Visit the merchant, make a purchase, and upload your receipt to earn your reward.
          </p>
        </div>
      </div>
    </div>
  )
}
