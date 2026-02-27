import { MapPin } from 'lucide-react'

interface DistanceCardProps {
  distanceMiles: number
  walkTimeLabel?: string  // e.g., "3 min walk"
  momentCopy?: string     // e.g., "Fits your charge window"
}

export function DistanceCard({ distanceMiles, walkTimeLabel, momentCopy }: DistanceCardProps) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
          <MapPin className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-900">{walkTimeLabel || `${distanceMiles.toFixed(1)} mi`}</p>
          <p className="text-sm text-gray-600">
            {distanceMiles.toFixed(1)} miles from charger
            {momentCopy && ` · ${momentCopy}`}
          </p>
        </div>
      </div>
    </div>
  )
}

