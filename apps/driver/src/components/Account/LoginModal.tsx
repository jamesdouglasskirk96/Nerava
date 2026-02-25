import { useState } from 'react'
import { X } from 'lucide-react'
import { teslaLoginStart, ApiError } from '../../services/auth'

interface LoginModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export function LoginModal({ isOpen, onClose, onSuccess: _onSuccess }: LoginModalProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleTeslaSignIn = async () => {
    setLoading(true)
    setError(null)

    try {
      const { authorization_url } = await teslaLoginStart()
      // In native iOS app, open Tesla auth in Safari (WKWebView can't handle it)
      // Universal Links will bring the user back to the app after auth
      if (window.neravaNative?.openExternalUrl) {
        window.neravaNative.openExternalUrl(authorization_url)
        // Reset loading after a moment since the user left the app
        setTimeout(() => setLoading(false), 2000)
      } else {
        window.location.href = authorization_url
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to start Tesla sign-in. Please try again.')
      }
      setLoading(false)
    }
  }

  const handleClose = () => {
    setError(null)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-[60] flex items-end sm:items-center justify-center">
      <div className="bg-white w-full sm:max-w-md sm:rounded-2xl rounded-t-2xl p-6 animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold">Sign in</h2>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tesla Sign-In */}
        <div className="text-center mb-6">
          <p className="text-[#65676B] text-sm">
            Sign in with your Tesla account to unlock charging rewards.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">
            {error}
          </div>
        )}

        <button
          onClick={handleTeslaSignIn}
          disabled={loading}
          className="w-full py-3 bg-[#171A20] text-white font-semibold rounded-xl hover:bg-[#393C41] disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-3"
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <svg className="w-5 h-5" viewBox="0 0 278.7 36.3" fill="currentColor">
                <path d="M238.1 14.4v21.9h7V21.7h25.6v-7.3h-32.6zm-29.5 0v21.9h7v-21.9h-7zm-17.8 0L178 30.2 165.2 14.4h-9.1v21.9h7V22.5l10.9 13.8h8.2l10.9-13.8v13.8h7V14.4h-9.3zM89.5 14.4v21.9h33.2v-7.3H96.5v-2h26.2v-6H96.5v-1.3h26.2v-5.3H89.5zm-15.7 0v21.9h7V14.4h-7zM42.5 21.4h16.1l-8-7-8.1 7zm-12.3 0L47 5.8l-3.6-3.1L17 25.1l3.6 3.1 3.1-2.7v10.8h7V21.4h-.5zm34.6 0l-3.1 2.7V13.3h-7v22.9h.5L72.5 52.8l3.6-3.1-6.5-5.6 16.7-14.4v-8.3h-.5z"/>
              </svg>
              Sign in with Tesla
            </>
          )}
        </button>

        <p className="text-xs text-[#65676B] text-center mt-4">
          By continuing, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  )
}
