import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { teslaLoginCallback, ApiError } from '../../services/auth'
import type { TeslaVehicle } from '../../services/auth'

export function TeslaCallbackScreen() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const code = searchParams.get('code')
    const state = searchParams.get('state')

    if (!code || !state) {
      setError('Missing authorization code. Please try signing in again.')

      return
    }

    teslaLoginCallback(code, state)
      .then((data) => {
        const vehicles: TeslaVehicle[] = data.vehicles || []

        if (vehicles.length === 1) {
          // Auto-select the only vehicle, go to home
          import('../../services/auth').then(({ teslaSelectVehicle }) => {
            teslaSelectVehicle(vehicles[0].id)
              .then(() => navigate('/', { replace: true }))
              .catch(() => navigate('/', { replace: true }))
          })
        } else if (vehicles.length > 1) {
          navigate('/select-vehicle', { state: { vehicles }, replace: true })
        } else {
          // No vehicles — go home anyway (connection is stored)
          navigate('/', { replace: true })
        }
      })
      .catch((err) => {
        if (err instanceof ApiError) {
          setError(err.message)
        } else {
          setError('Tesla sign-in failed. Please try again.')
        }
  
      })
  }, [searchParams, navigate])

  if (error) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center px-6">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h2 className="text-xl font-bold mb-2">Sign-in failed</h2>
        <p className="text-[#65676B] text-center mb-6">{error}</p>
        <button
          onClick={() => navigate('/', { replace: true })}
          className="px-6 py-3 bg-[#171A20] text-white font-semibold rounded-xl hover:bg-[#393C41] transition-colors"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center">
      <div className="w-8 h-8 border-3 border-[#171A20] border-t-transparent rounded-full animate-spin mb-4" />
      <p className="text-[#65676B]">Signing in with Tesla...</p>
    </div>
  )
}
