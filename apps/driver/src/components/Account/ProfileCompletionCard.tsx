import { useState } from 'react'
import { User, X } from 'lucide-react'
import { api } from '../../services/api'

interface ProfileCompletionCardProps {
  currentEmail?: string | null
  currentName?: string | null
  onProfileUpdated: (updates: { email?: string; display_name?: string }) => void
}

export function ProfileCompletionCard({ currentEmail, currentName, onProfileUpdated }: ProfileCompletionCardProps) {
  const [displayName, setDisplayName] = useState(currentName || '')
  const [email, setEmail] = useState(currentEmail || '')
  const [saving, setSaving] = useState(false)
  const [dismissed, setDismissed] = useState(() => {
    return localStorage.getItem('nerava_profile_dismissed') === 'true'
  })

  // Don't show if already complete or dismissed
  if (dismissed || (currentEmail && currentName)) return null

  const handleSave = async () => {
    setSaving(true)
    try {
      const updates: { email?: string; display_name?: string } = {}
      if (!currentName && displayName.trim()) updates.display_name = displayName.trim()
      if (!currentEmail && email.trim()) updates.email = email.trim()

      if (Object.keys(updates).length > 0) {
        await api.put('/v1/account/profile', updates)
        // Update localStorage
        const stored = localStorage.getItem('nerava_user')
        if (stored) {
          const user = JSON.parse(stored)
          if (updates.display_name) user.name = updates.display_name
          if (updates.email) user.email = updates.email
          localStorage.setItem('nerava_user', JSON.stringify(user))
        }
        onProfileUpdated(updates)
      }
    } catch (e) {
      console.error('Failed to update profile:', e)
    } finally {
      setSaving(false)
    }
  }

  const handleDismiss = () => {
    setDismissed(true)
    localStorage.setItem('nerava_profile_dismissed', 'true')
  }

  return (
    <div className="bg-amber-50 rounded-2xl p-4 border border-amber-200 relative">
      <button
        onClick={handleDismiss}
        className="absolute top-3 right-3 p-1 hover:bg-amber-100 rounded-full"
        aria-label="Dismiss"
      >
        <X className="w-4 h-4 text-amber-600" />
      </button>

      <div className="flex items-center gap-2 mb-3">
        <User className="w-5 h-5 text-amber-700" />
        <h3 className="font-semibold text-sm text-amber-900">Complete Your Profile</h3>
      </div>

      <div className="space-y-2">
        {!currentName && (
          <input
            type="text"
            placeholder="Display name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full px-3 py-2 text-base border border-amber-200 rounded-xl bg-white focus:outline-none focus:border-amber-400"
          />
        )}
        {!currentEmail && (
          <input
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 text-base border border-amber-200 rounded-xl bg-white focus:outline-none focus:border-amber-400"
          />
        )}
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="mt-3 w-full py-2 bg-amber-600 text-white text-sm font-medium rounded-xl hover:bg-amber-700 active:scale-[0.98] transition-all disabled:opacity-50"
      >
        {saving ? 'Saving...' : 'Save'}
      </button>
    </div>
  )
}
