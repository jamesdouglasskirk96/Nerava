import { MapPin } from 'lucide-react'

interface LocationStatusCardProps {
  geo: {
    loading: boolean
    error: string | null
    distanceToCharger: number | null
    isNearCharger: boolean
  }
}

export function LocationStatusCard({ geo }: LocationStatusCardProps) {
  // Loading state
  if (geo.loading) {
    return (
      <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center animate-pulse">
          <MapPin className="w-5 h-5 text-gray-400" />
        </div>
        <p className="text-sm text-gray-500">Getting your location...</p>
      </div>
    )
  }

  // Error or permission denied - CALM treatment
  if (geo.error || geo.distanceToCharger === null) {
    return (
      <div className="flex items-center gap-3 p-2.5 bg-gray-50 rounded-xl">
        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
          <MapPin className="w-4 h-4 text-gray-400" />
        </div>
        <div className="flex-1">
          <p className="text-xs font-medium text-gray-600">Location off</p>
          <p className="text-[11px] text-gray-500">
            Enable location to verify you're at the charger.
          </p>
        </div>
      </div>
    )
  }

  // Near charger - success state
  if (geo.isNearCharger) {
    return (
      <div className="flex items-center gap-3 p-3 bg-green-50 rounded-xl">
        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
          <MapPin className="w-5 h-5 text-green-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-green-700">You're at the charger</p>
          <p className="text-xs text-green-600">{Math.round(geo.distanceToCharger)}m away</p>
        </div>
      </div>
    )
  }

  // Not near charger
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
        <MapPin className="w-5 h-5 text-blue-600" />
      </div>
      <div>
        <p className="text-sm font-medium text-gray-700">Distance</p>
        <p className="text-xs text-gray-500">{Math.round(geo.distanceToCharger)}m to charger</p>
      </div>
    </div>
  )
}

