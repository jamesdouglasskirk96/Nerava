import { useState } from 'react'
import { Button } from '../shared/Button'
import { modalBackdropOpacity } from '../../ui/tokens'

interface ExclusiveCompletedModalProps {
  onContinue: (feedback?: { thumbsUp: boolean }) => void
}

export function ExclusiveCompletedModal({
  onContinue,
}: ExclusiveCompletedModalProps) {
  const [selectedFeedback, setSelectedFeedback] = useState<'up' | 'down' | null>(null)

  const handleContinue = () => {
    if (selectedFeedback) {
      onContinue({ thumbsUp: selectedFeedback === 'up' })
    } else {
      onContinue()
    }
  }

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
        {/* Success checkmark icon */}
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
                strokeWidth={3}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
          Exclusive Completed
        </h2>

        {/* Subtitle */}
        <p className="text-gray-600 text-center mb-6">
          Thanks for charging with Nerava
        </p>

        {/* Feedback question */}
        <p className="text-gray-700 text-center mb-4">
          Did this match what you wanted?
        </p>

        {/* Thumbs up/down buttons */}
        <div className="flex justify-center gap-6 mb-6">
          <button
            type="button"
            onClick={() => setSelectedFeedback('up')}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
              selectedFeedback === 'up'
                ? 'bg-green-100 ring-2 ring-green-500'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            <svg
              className={`w-6 h-6 ${selectedFeedback === 'up' ? 'text-green-600' : 'text-gray-500'}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
              />
            </svg>
          </button>
          <button
            type="button"
            onClick={() => setSelectedFeedback('down')}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
              selectedFeedback === 'down'
                ? 'bg-red-100 ring-2 ring-red-500'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            <svg
              className={`w-6 h-6 ${selectedFeedback === 'down' ? 'text-red-600' : 'text-gray-500'}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"
              />
            </svg>
          </button>
        </div>

        {/* Continue button */}
        <Button
          variant="primary"
          className="w-full"
          onClick={handleContinue}
        >
          Continue
        </Button>
      </div>
    </div>
  )
}
