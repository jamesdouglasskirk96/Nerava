import { useState } from 'react'
import { X, Users, Send } from 'lucide-react'
import { Button } from '../shared/Button'

const INTEREST_TAGS = [
  { id: 'coffee', label: 'Coffee', emoji: '' },
  { id: 'food', label: 'Food', emoji: '' },
  { id: 'discount', label: 'Discount', emoji: '' },
  { id: 'workspace', label: 'Workspace', emoji: '' },
  { id: 'safety', label: 'Safety Stop', emoji: '' },
  { id: 'shopping', label: 'Shopping', emoji: '' },
]

interface RequestToJoinSheetProps {
  isOpen: boolean
  merchantName: string
  requestCount: number
  onClose: () => void
  onSubmit: (tags: string[]) => Promise<void>
}

export function RequestToJoinSheet({
  isOpen,
  merchantName,
  requestCount,
  onClose,
  onSubmit,
}: RequestToJoinSheetProps) {
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  if (!isOpen) return null

  const toggleTag = (id: string) => {
    setSelectedTags(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    )
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      await onSubmit(selectedTags)
      setSubmitted(true)
    } catch (err) {
      console.error('Failed to submit request:', err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40">
      <div className="w-full max-w-lg bg-white rounded-t-3xl p-6 pb-8 animate-slide-up">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-xl font-semibold text-[#050505]">
            {submitted ? 'Request Sent!' : 'Request to Join'}
          </h3>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {submitted ? (
          <div className="text-center py-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Send className="w-8 h-8 text-green-600" />
            </div>
            <p className="text-[#050505] font-medium mb-2">
              We'll reach out to {merchantName}
            </p>
            <p className="text-sm text-[#65676B] mb-4">
              You'll be notified if they join Nerava with exclusive offers for EV drivers.
            </p>
            {requestCount > 1 && (
              <div className="flex items-center justify-center gap-1.5 text-sm text-[#65676B]">
                <Users className="w-4 h-4" />
                <span>{requestCount} drivers have requested this merchant</span>
              </div>
            )}
            <Button variant="primary" className="w-full mt-6" onClick={onClose}>
              Done
            </Button>
          </div>
        ) : (
          <>
            <p className="text-sm text-[#65676B] mb-5">
              Tell us what would make you visit <span className="font-medium text-[#050505]">{merchantName}</span> while charging.
            </p>

            <div className="flex flex-wrap gap-2 mb-6">
              {INTEREST_TAGS.map(tag => (
                <button
                  key={tag.id}
                  onClick={() => toggleTag(tag.id)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    selectedTags.includes(tag.id)
                      ? 'bg-[#050505] text-white'
                      : 'bg-[#F0F2F5] text-[#050505] hover:bg-[#E4E6EB]'
                  }`}
                >
                  {tag.label}
                </button>
              ))}
            </div>

            {requestCount > 0 && (
              <div className="flex items-center gap-1.5 text-sm text-[#65676B] mb-4">
                <Users className="w-4 h-4" />
                <span>{requestCount} {requestCount === 1 ? 'driver has' : 'drivers have'} requested this merchant</span>
              </div>
            )}

            <Button
              variant="primary"
              className="w-full"
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? 'Sending...' : 'Send Request'}
            </Button>
          </>
        )}
      </div>
    </div>
  )
}
