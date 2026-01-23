// Preferences modal - "Want better matches next time?"
import { useState } from 'react'

export type PreferenceType =
  | 'Coffee'
  | 'Food'
  | 'Fitness'
  | 'Retail'
  | 'Pets'
  | 'Kids'
  | 'Accessibility'
  | 'Morning'
  | 'Midday'
  | 'Evening'

interface PreferencesModalProps {
  isOpen: boolean
  onClose: () => void
  onSave?: (preferences: PreferenceType[]) => void
}

const ROW_1_PREFERENCES: PreferenceType[] = ['Coffee', 'Food', 'Fitness', 'Retail', 'Pets', 'Kids', 'Accessibility']
const ROW_2_PREFERENCES: PreferenceType[] = ['Morning', 'Midday', 'Evening']

function loadSavedPreferences(): PreferenceType[] {
  const saved = localStorage.getItem('user_preferences')
  if (saved) {
    try {
      return JSON.parse(saved) as PreferenceType[]
    } catch {
      // Invalid JSON, start fresh
    }
  }
  return []
}

// Inner content component - mounts fresh each time modal opens
function PreferencesModalContent({
  onClose,
  onSave,
}: {
  onClose: () => void
  onSave?: (preferences: PreferenceType[]) => void
}) {
  // Load saved preferences from localStorage when component mounts
  const [selectedPreferences, setSelectedPreferences] = useState<PreferenceType[]>(loadSavedPreferences)

  const handlePreferenceSelect = (preference: PreferenceType) => {
    setSelectedPreferences((prev) => {
      if (prev.includes(preference)) {
        return prev.filter((p) => p !== preference)
      }
      return [...prev, preference]
    })
  }

  const handleSave = () => {
    // Save to localStorage
    localStorage.setItem('user_preferences', JSON.stringify(selectedPreferences))

    // Call onSave callback if provided
    if (onSave) {
      onSave(selectedPreferences)
    }

    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[60] p-4">
      <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
        {/* Title */}
        <h2 className="text-xl text-center mb-6">Want better matches next time?</h2>

        {/* Preference Chips - Row 1 */}
        <div className="flex flex-wrap gap-2 mb-3 justify-center">
          {ROW_1_PREFERENCES.map((pref) => (
            <button
              key={pref}
              onClick={() => handlePreferenceSelect(pref)}
              className={`px-4 py-2 rounded-full font-medium text-sm transition-all active:scale-95 ${
                selectedPreferences.includes(pref)
                  ? 'bg-[#1877F2] text-white'
                  : 'bg-[#F7F8FA] text-[#050505] border border-[#E4E6EB]'
              }`}
            >
              {pref}
            </button>
          ))}
        </div>

        {/* Preference Chips - Row 2 */}
        <div className="flex flex-wrap gap-2 mb-6 justify-center">
          {ROW_2_PREFERENCES.map((pref) => (
            <button
              key={pref}
              onClick={() => handlePreferenceSelect(pref)}
              className={`px-4 py-2 rounded-full font-medium text-sm transition-all active:scale-95 ${
                selectedPreferences.includes(pref)
                  ? 'bg-[#1877F2] text-white'
                  : 'bg-[#F7F8FA] text-[#050505] border border-[#E4E6EB]'
              }`}
            >
              {pref}
            </button>
          ))}
        </div>

        {/* Done Button */}
        <button
          onClick={handleSave}
          className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
        >
          Done
        </button>
      </div>
    </div>
  )
}

export function PreferencesModal({ isOpen, onClose, onSave }: PreferencesModalProps) {
  if (!isOpen) return null

  // Content component mounts fresh each time modal opens
  return <PreferencesModalContent onClose={onClose} onSave={onSave} />
}
