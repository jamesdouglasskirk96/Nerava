import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'

export function MagicLinkPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = searchParams.get('token')

    if (!token) {
      setStatus('error')
      setError('Invalid magic link')
      return
    }

    // Verify the magic link with backend
    fetch(`https://api.nerava.network/v1/magic/verify?token=${token}`, {
      method: 'GET',
      redirect: 'follow',
    })
      .then((response) => {
        if (response.redirected) {
          // Backend redirected us - follow the redirect
          window.location.href = response.url
        } else if (!response.ok) {
          throw new Error('Invalid or expired link')
        }
      })
      .catch((err) => {
        setStatus('error')
        setError(err.message)
      })
  }, [searchParams])

  if (status === 'verifying') {
    return (
      <div className="h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Verifying your link...</p>
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="h-screen flex items-center justify-center bg-white">
        <div className="text-center p-6">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h1 className="text-xl font-bold mb-2">Link Expired</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg"
          >
            Go to Home
          </button>
        </div>
      </div>
    )
  }

  return null
}


