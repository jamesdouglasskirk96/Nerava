import { useState, useEffect } from 'react'
import { ArrowLeft, Bell, Mail, MessageSquare, Megaphone } from 'lucide-react'
import { fetchAPI } from '../../services/api'

interface SettingsViewProps {
  onBack: () => void
}

export function SettingsView({ onBack }: SettingsViewProps) {
  const [prefs, setPrefs] = useState({
    earned_nova: true,
    nearby_nova: true,
    wallet_reminders: true,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const loadPrefs = async () => {
      try {
        const data = await fetchAPI<typeof prefs>('/v1/notifications/prefs')
        setPrefs(data)
      } catch {
        // Use defaults
      } finally {
        setLoading(false)
      }
    }
    loadPrefs()
  }, [])

  const updatePref = async (key: keyof typeof prefs, value: boolean) => {
    const newPrefs = { ...prefs, [key]: value }
    setPrefs(newPrefs)
    setSaving(true)

    try {
      await fetchAPI('/v1/notifications/prefs', {
        method: 'PUT',
        body: JSON.stringify(newPrefs)
      })
    } catch {
      // Revert on error
      setPrefs(prefs)
    } finally {
      setSaving(false)
    }
  }

  const toggleItems = [
    { key: 'earned_nova' as const, label: 'Earned Nova', icon: Bell, description: 'Get notified when you earn Nova rewards' },
    { key: 'nearby_nova' as const, label: 'Nearby Nova', icon: Mail, description: 'Receive alerts about Nova opportunities nearby' },
    { key: 'wallet_reminders' as const, label: 'Wallet Reminders', icon: MessageSquare, description: 'Reminders about wallet activations and exclusives' },
  ]

  return (
    <div className="h-[100dvh] flex flex-col bg-white">
      <header className="px-5 h-[60px] flex items-center border-b border-[#E4E6EB]">
        <button onClick={onBack} className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="ml-4 text-lg font-medium">Settings</h1>
        {saving && <span className="ml-auto text-sm text-[#65676B]">Saving...</span>}
      </header>

      <div className="flex-1 overflow-y-auto p-5">
        <h2 className="text-sm font-medium text-[#65676B] uppercase mb-4">Notifications</h2>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin w-6 h-6 border-2 border-[#1877F2] border-t-transparent rounded-full" />
          </div>
        ) : (
          <div className="space-y-4">
            {toggleItems.map(({ key, label, icon: Icon, description }) => (
              <div key={key} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <Icon className="w-5 h-5 text-[#65676B]" />
                  <div>
                    <p className="font-medium text-[#050505]">{label}</p>
                    <p className="text-sm text-[#65676B]">{description}</p>
                  </div>
                </div>
                <button
                  onClick={() => updatePref(key, !prefs[key])}
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    prefs[key] ? 'bg-[#1877F2]' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                      prefs[key] ? 'translate-x-5' : ''
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}


