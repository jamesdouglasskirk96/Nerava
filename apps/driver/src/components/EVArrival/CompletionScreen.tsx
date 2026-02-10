import { useState } from 'react'
import { capture } from '../../analytics'
import { DRIVER_EVENTS } from '../../analytics/events'

const DOWN_REASONS = [
  { id: 'wrong_hours', label: 'Wrong hours' },
  { id: 'too_crowded', label: 'Too crowded' },
  { id: 'slow_service', label: 'Slow service' },
  { id: 'other', label: 'Other' },
]

interface CompletionScreenProps {
  merchantName: string
  arrivalType: string
  orderNumber?: string | null
  onSubmitFeedback: (rating: string, reason?: string, comment?: string) => void
  onDone: () => void
}

export function CompletionScreen({
  merchantName,
  arrivalType,
  orderNumber,
  onSubmitFeedback,
  onDone,
}: CompletionScreenProps) {
  const [rating, setRating] = useState<'up' | 'down' | null>(null)
  const [reason, setReason] = useState<string | null>(null)
  const [comment, setComment] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const modeLabel = arrivalType === 'ev_curbside' ? 'EV Curbside' : 'EV Dine-In'

  const handleSubmit = () => {
    if (!rating) return
    capture(DRIVER_EVENTS.EV_ARRIVAL_FEEDBACK_SUBMITTED, {
      rating,
      reason: reason || undefined,
    })
    onSubmitFeedback(rating, reason || undefined, comment || undefined)
    setSubmitted(true)
  }

  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-1">Thanks for the feedback!</h2>
        <p className="text-gray-500 mb-6">Your experience helps improve Nerava.</p>
        <button
          onClick={onDone}
          className="bg-blue-600 text-white px-8 py-3 rounded-xl font-semibold"
        >
          Done
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center px-6 pt-12 pb-8">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
        <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>

      <h2 className="text-xl font-bold text-gray-900 mb-1">Visit Complete</h2>
      <p className="text-gray-600 mb-1">{merchantName}</p>
      <p className="text-sm text-gray-400 mb-6">
        {modeLabel}{orderNumber ? ` · Order #${orderNumber}` : ''}
      </p>

      <p className="text-gray-700 font-medium mb-4">How was your experience?</p>

      <div className="flex gap-6 mb-6">
        <button
          onClick={() => { setRating('up'); setReason(null) }}
          className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl border-2 transition-colors ${
            rating === 'up' ? 'border-green-500 bg-green-50' : 'border-gray-200'
          }`}
          aria-label="Thumbs up"
        >
          👍
        </button>
        <button
          onClick={() => { setRating('down'); setComment('') }}
          className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl border-2 transition-colors ${
            rating === 'down' ? 'border-red-500 bg-red-50' : 'border-gray-200'
          }`}
          aria-label="Thumbs down"
        >
          👎
        </button>
      </div>

      {/* Thumbs down: reason chips */}
      {rating === 'down' && (
        <div className="w-full max-w-sm mb-6">
          <div className="flex flex-wrap gap-2 justify-center">
            {DOWN_REASONS.map(r => (
              <button
                key={r.id}
                onClick={() => setReason(r.id)}
                className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                  reason === r.id
                    ? 'bg-red-600 text-white border-red-600'
                    : 'bg-white text-gray-600 border-gray-200'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Thumbs up: optional comment */}
      {rating === 'up' && (
        <div className="w-full max-w-sm mb-6">
          <textarea
            value={comment}
            onChange={e => setComment(e.target.value.slice(0, 140))}
            placeholder="What did you love? (optional)"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 text-sm resize-none"
            rows={3}
            maxLength={140}
          />
          <p className="text-xs text-gray-400 text-right mt-1">{comment.length}/140</p>
        </div>
      )}

      {rating && (
        <button
          onClick={handleSubmit}
          className="w-full max-w-sm bg-blue-600 text-white py-3 rounded-xl font-semibold"
        >
          Done
        </button>
      )}

      {/* Skip feedback */}
      {!rating && (
        <button
          onClick={onDone}
          className="text-gray-400 text-sm mt-4"
        >
          Skip
        </button>
      )}
    </div>
  )
}
