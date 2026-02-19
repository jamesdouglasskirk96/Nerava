import { Coffee, Utensils, Laptop } from 'lucide-react'
import { useState, useEffect } from 'react'
import { FEATURE_FLAGS } from '../../config/featureFlags'

export type RefuelIntent = 'eat' | 'work' | 'quick-stop'

export interface RefuelDetails {
  intent: RefuelIntent
  partySize?: number
  needsPowerOutlet?: boolean
  isToGo?: boolean
}

interface RefuelIntentModalProps {
  merchantName: string
  isOpen: boolean
  onConfirm: (details: RefuelDetails) => void
  onClose: () => void
}

const STORAGE_KEY = 'nerava_last_intent'

export function RefuelIntentModal({ merchantName, isOpen, onConfirm, onClose }: RefuelIntentModalProps) {
  const [selectedIntent, setSelectedIntent] = useState<RefuelIntent | null>(null)
  const [partySize, setPartySize] = useState(1)
  const [needsPowerOutlet, setNeedsPowerOutlet] = useState(false)
  const [isToGo, setIsToGo] = useState(false)

  // Load previous intent from localStorage when modal opens
  useEffect(() => {
    if (isOpen && FEATURE_FLAGS.LIVE_COORDINATION_UI_V1) {
      try {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) {
          const previousIntent: RefuelDetails = JSON.parse(stored)
          setSelectedIntent(previousIntent.intent)
          if (previousIntent.partySize) setPartySize(previousIntent.partySize)
          if (previousIntent.needsPowerOutlet !== undefined) setNeedsPowerOutlet(previousIntent.needsPowerOutlet)
          if (previousIntent.isToGo !== undefined) setIsToGo(previousIntent.isToGo)
        }
      } catch (error) {
        // Invalid JSON, ignore and use defaults
        console.warn('Failed to load previous intent from localStorage:', error)
      }
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleContinue = () => {
    if (!selectedIntent) return

    const details: RefuelDetails = {
      intent: selectedIntent,
      ...(selectedIntent === 'eat' && { partySize }),
      ...(selectedIntent === 'work' && { needsPowerOutlet }),
      ...(selectedIntent === 'quick-stop' && { isToGo }),
    }

    // Save to localStorage for next time
    if (FEATURE_FLAGS.LIVE_COORDINATION_UI_V1) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(details))
      } catch (error) {
        console.warn('Failed to save intent to localStorage:', error)
      }
    }

    onConfirm(details)
  }

  const intentOptions = [
    {
      id: 'eat' as const,
      icon: Utensils,
      title: 'Eat',
      description: 'Dine-in or grab a meal',
    },
    {
      id: 'work' as const,
      icon: Laptop,
      title: 'Work',
      description: 'Need a workspace or WiFi',
    },
    {
      id: 'quick-stop' as const,
      icon: Coffee,
      title: 'Quick Stop',
      description: 'Coffee, restroom, or to-go',
    },
  ]

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="refuel-intent-title"
    >
      <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl">
        {/* Header */}
        <div className="mb-6">
          <h2 id="refuel-intent-title" className="text-2xl text-center mb-2">
            How are you refueling?
          </h2>
          <p className="text-sm text-[#65676B] text-center">
            This helps {merchantName} prepare for your arrival
          </p>
        </div>

        {/* Intent Options */}
        <div className="space-y-3 mb-6" role="radiogroup" aria-label="Refuel intent options">
          {intentOptions.map((option) => {
            const Icon = option.icon
            const isSelected = selectedIntent === option.id

            return (
              <button
                key={option.id}
                onClick={() => setSelectedIntent(option.id)}
                role="radio"
                aria-checked={isSelected}
                className={`w-full p-4 rounded-2xl border-2 transition-all text-left ${
                  isSelected
                    ? 'border-[#1877F2] bg-[#1877F2]/5'
                    : 'border-[#E4E6EB] hover:border-[#1877F2]/30'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                    isSelected ? 'bg-[#1877F2]' : 'bg-[#F7F8FA]'
                  }`}>
                    <Icon className={`w-5 h-5 ${
                      isSelected ? 'text-white' : 'text-[#65676B]'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-base mb-1">{option.title}</h3>
                    <p className="text-sm text-[#65676B]">{option.description}</p>
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        {/* Sub-options based on intent */}
        {selectedIntent === 'eat' && (
          <div className="mb-6 bg-[#F7F8FA] rounded-2xl p-4">
            <label className="text-sm font-medium mb-3 block" id="party-size-label">Party Size</label>
            <div className="flex gap-2" role="group" aria-labelledby="party-size-label">
              {[1, 2, 3, 4, 5].map((size) => (
                <button
                  key={size}
                  onClick={() => setPartySize(size)}
                  aria-pressed={partySize === size}
                  className={`flex-1 py-2 px-3 rounded-xl font-medium transition-all ${
                    partySize === size
                      ? 'bg-[#1877F2] text-white'
                      : 'bg-white text-[#050505] border border-[#E4E6EB]'
                  }`}
                >
                  {size === 5 ? '5+' : size}
                </button>
              ))}
            </div>
          </div>
        )}

        {selectedIntent === 'work' && (
          <div className="mb-6 bg-[#F7F8FA] rounded-2xl p-4">
            <button
              onClick={() => setNeedsPowerOutlet(!needsPowerOutlet)}
              aria-pressed={needsPowerOutlet}
              className={`w-full py-3 rounded-xl font-medium transition-all ${
                needsPowerOutlet
                  ? 'bg-[#1877F2] text-white'
                  : 'bg-white text-[#050505] border border-[#E4E6EB]'
              }`}
            >
              {needsPowerOutlet ? '✓ ' : ''}Need Power Outlet
            </button>
          </div>
        )}

        {selectedIntent === 'quick-stop' && (
          <div className="mb-6 bg-[#F7F8FA] rounded-2xl p-4">
            <button
              onClick={() => setIsToGo(!isToGo)}
              aria-pressed={isToGo}
              className={`w-full py-3 rounded-xl font-medium transition-all ${
                isToGo
                  ? 'bg-[#1877F2] text-white'
                  : 'bg-white text-[#050505] border border-[#E4E6EB]'
              }`}
            >
              {isToGo ? '✓ ' : ''}To-Go Order
            </button>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-3">
          <button
            onClick={handleContinue}
            disabled={!selectedIntent}
            className={`w-full py-4 rounded-2xl font-medium transition-all ${
              selectedIntent
                ? 'bg-[#1877F2] text-white hover:bg-[#166FE5] active:scale-[0.98]'
                : 'bg-[#E4E6EB] text-[#65676B] cursor-not-allowed'
            }`}
          >
            Continue
          </button>
          <button
            onClick={onClose}
            className="w-full py-4 bg-white border-2 border-[#E4E6EB] text-[#050505] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-[0.98] transition-all"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
