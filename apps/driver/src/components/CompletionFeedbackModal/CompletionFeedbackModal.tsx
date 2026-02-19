// Completion Feedback Modal - "Exclusive Completed"
import { CheckCircle, ThumbsUp, ThumbsDown } from 'lucide-react'
import { useState } from 'react'

interface CompletionFeedbackModalProps {
  isOpen: boolean
  onContinue: () => void
}

/**
 * Modal shown after exclusive completion
 * Thumbs up / down feedback
 * CTA: "Continue" → triggers preferences modal
 */
export function CompletionFeedbackModal({
  isOpen,
  onContinue,
}: CompletionFeedbackModalProps) {
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
      <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
        {/* Icon */}
        <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="w-8 h-8 text-[#1877F2]" />
        </div>

        {/* Title */}
        <h2 className="text-2xl text-center mb-3">Exclusive Completed</h2>

        {/* Description */}
        <p className="text-center text-[#65676B] mb-6">
          Thanks for charging with Nerava
        </p>

        {/* Feedback */}
        <div className="mb-6">
          <p className="text-center text-sm text-[#65676B] mb-3">
            Did this match what you wanted?
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => setFeedback('positive')}
              className={`w-16 h-16 rounded-full flex items-center justify-center transition-all active:scale-95 ${
                feedback === 'positive'
                  ? 'bg-green-100 text-green-600'
                  : 'bg-[#F7F8FA] text-[#65676B] hover:bg-green-50'
              }`}
              aria-label="Positive feedback"
            >
              <ThumbsUp className="w-6 h-6" aria-hidden="true" />
            </button>
            <button
              onClick={() => setFeedback('negative')}
              className={`w-16 h-16 rounded-full flex items-center justify-center transition-all active:scale-95 ${
                feedback === 'negative'
                  ? 'bg-red-100 text-red-600'
                  : 'bg-[#F7F8FA] text-[#65676B] hover:bg-red-50'
              }`}
              aria-label="Negative feedback"
            >
              <ThumbsDown className="w-6 h-6" aria-hidden="true" />
            </button>
          </div>
        </div>

        {/* Button */}
        <button
          onClick={onContinue}
          className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
        >
          Continue
        </button>
      </div>
    </div>
  )
}

