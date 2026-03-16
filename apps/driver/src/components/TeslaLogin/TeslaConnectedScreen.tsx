import { useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'

export function TeslaConnectedScreen() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const error = searchParams.get('error')

  useEffect(() => {
    // Invalidate tesla-status cache so DriverHome picks up the new connection
    queryClient.invalidateQueries({ queryKey: ['tesla-status'] })

    // Auto-redirect to home after a brief delay
    const timer = setTimeout(() => {
      navigate('/', { replace: true })
    }, 2000)
    return () => clearTimeout(timer)
  }, [navigate, queryClient])

  if (error) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center px-6">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h2 className="text-xl font-bold mb-2">Connection failed</h2>
        <p className="text-[#65676B] text-center mb-6">Could not connect your Tesla account. Please try again.</p>
        <button
          onClick={() => navigate('/', { replace: true })}
          className="px-6 py-3 bg-[#171A20] text-white font-semibold rounded-xl hover:bg-[#393C41] transition-colors"
        >
          Go home
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-6">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
        <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h2 className="text-xl font-bold mb-2">Tesla connected</h2>
      <p className="text-[#65676B] text-center">Redirecting to home...</p>
    </div>
  )
}
