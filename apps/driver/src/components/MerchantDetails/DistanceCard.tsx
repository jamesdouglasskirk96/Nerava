import { MapPin } from 'lucide-react'

interface DistanceCardProps {
  distanceMiles: number
  walkTimeLabel?: string  // e.g., "3 min walk"
}

export function DistanceCard({ distanceMiles, walkTimeLabel }: DistanceCardProps) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
      <div className="flex items-center gap-3">
        <MapPin className="w-5 h-5 text-gray-600 flex-shrink-0" />
        <div>
          <p className="text-xs text-gray-500 mb-1.5 font-medium uppercase tracking-wide">Distance</p>
          <p className="text-sm text-gray-900">
            {distanceMiles.toFixed(1)} miles
            {walkTimeLabel && ` · ${walkTimeLabel}`}
          </p>
        </div>
      </div>
    </div>
  )
}

