import { X, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { Button } from '../shared/Button'
import type { ReceiptUploadResponse } from '../../types'

interface ReceiptResultModalProps {
  isOpen: boolean
  result: ReceiptUploadResponse
  merchantName: string
  onClose: () => void
}

export function ReceiptResultModal({
  isOpen,
  result,
  merchantName,
  onClose,
}: ReceiptResultModalProps) {
  if (!isOpen) return null

  const isApproved = result.status === 'approved'
  const isRejected = result.status === 'rejected'
  const isPending = result.status === 'pending' || result.status === 'processing'

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40">
      <div className="w-full max-w-lg bg-white rounded-t-3xl p-6 pb-8 animate-slide-up">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-xl font-semibold text-[#050505]">Receipt Status</h3>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <div className="text-center py-4">
          {isApproved && (
            <>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <p className="text-lg font-semibold text-[#050505] mb-2">Receipt Verified!</p>
              <p className="text-sm text-[#65676B] mb-2">
                Your visit to {merchantName} has been confirmed.
              </p>
              {result.approved_reward_cents != null && result.approved_reward_cents > 0 && (
                <p className="text-lg font-bold text-green-600 mb-4">
                  +${(result.approved_reward_cents / 100).toFixed(2)} earned
                </p>
              )}
            </>
          )}

          {isRejected && (
            <>
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <XCircle className="w-8 h-8 text-red-600" />
              </div>
              <p className="text-lg font-semibold text-[#050505] mb-2">Receipt Not Verified</p>
              <p className="text-sm text-[#65676B] mb-4">
                {result.rejection_reason || `We couldn't verify your receipt from ${merchantName}. Please ensure the receipt is clear and includes the merchant name and total.`}
              </p>
            </>
          )}

          {isPending && (
            <>
              <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Clock className="w-8 h-8 text-amber-600" />
              </div>
              <p className="text-lg font-semibold text-[#050505] mb-2">Under Review</p>
              <p className="text-sm text-[#65676B] mb-4">
                Your receipt is being reviewed. You'll be notified once it's verified.
              </p>
            </>
          )}

          <Button variant="primary" className="w-full mt-4" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </div>
  )
}
