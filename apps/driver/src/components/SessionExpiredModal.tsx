import { useEffect, useState } from 'react'

export function SessionExpiredModal() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const handler = () => setVisible(true)
    window.addEventListener('nerava:session-expired', handler)
    return () => window.removeEventListener('nerava:session-expired', handler)
  }, [])

  if (!visible) return null

  const handleLogin = () => {
    setVisible(false)
    // Clear stale tokens and reload to trigger login flow
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    window.location.reload()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-6">
      <div className="bg-white rounded-2xl p-6 max-w-sm w-full text-center shadow-xl">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Session Expired
        </h2>
        <p className="text-gray-600 mb-6">
          Your session has expired. Please log in again to continue.
        </p>
        <button
          onClick={handleLogin}
          className="w-full px-6 py-3 bg-black text-white rounded-xl font-medium"
        >
          Log In
        </button>
      </div>
    </div>
  )
}
