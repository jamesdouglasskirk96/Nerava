import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { teslaSelectVehicle, ApiError } from '../../services/auth'
import type { TeslaVehicle } from '../../services/auth'

export function VehicleSelectScreen() {
  const location = useLocation()
  const navigate = useNavigate()
  const vehicles: TeslaVehicle[] = (location.state as any)?.vehicles || []
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSelect = async (vehicle: TeslaVehicle) => {
    setLoading(vehicle.id)
    setError(null)

    try {
      await teslaSelectVehicle(vehicle.id)
      // Request always-on location via native bridge if available
      if (window.neravaNative?.requestAlwaysLocation) {
        window.neravaNative.requestAlwaysLocation()
      }
      navigate('/', { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to select vehicle. Please try again.')
      }
      setLoading(null)
    }
  }

  if (vehicles.length === 0) {
    // No vehicles passed — redirect home
    navigate('/', { replace: true })
    return null
  }

  return (
    <div className="min-h-screen bg-white flex flex-col" style={{ height: 'var(--app-height, 100dvh)' }}>
      <header className="bg-white border-b border-[#E4E6EB] px-5 py-4">
        <h1 className="text-xl font-bold text-[#050505]">Select your vehicle</h1>
        <p className="text-sm text-[#65676B] mt-1">
          Choose which Tesla to use with Nerava
        </p>
      </header>

      <main className="flex-1 px-5 py-4 space-y-3">
        {error && (
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">
            {error}
          </div>
        )}

        {vehicles.map((vehicle) => (
          <button
            key={vehicle.id}
            onClick={() => handleSelect(vehicle)}
            disabled={loading !== null}
            className="w-full p-4 bg-white border border-[#E4E6EB] rounded-xl hover:border-[#171A20] transition-colors text-left flex items-center gap-4 disabled:opacity-50"
          >
            <div className="w-12 h-12 bg-[#F7F8FA] rounded-full flex items-center justify-center flex-shrink-0">
              <svg className="w-6 h-6 text-[#171A20]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10m10 0H3m10 0h2m4 0a1 1 0 001-1v-5a1 1 0 00-.3-.7l-4-4A1 1 0 0015 5h-2v11m4 0H13" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-[#050505] truncate">
                {vehicle.display_name || 'My Tesla'}
              </p>
              <p className="text-sm text-[#65676B]">
                {vehicle.model || 'Tesla'}{vehicle.vin ? ` \u00b7 ...${vehicle.vin.slice(-4)}` : ''}
              </p>
            </div>
            {loading === vehicle.id ? (
              <div className="w-5 h-5 border-2 border-[#171A20] border-t-transparent rounded-full animate-spin flex-shrink-0" />
            ) : (
              <svg className="w-5 h-5 text-[#65676B] flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
          </button>
        ))}
      </main>
    </div>
  )
}
