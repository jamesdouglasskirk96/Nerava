import { MapPin } from 'lucide-react'

interface DistanceCardProps {
  distanceMiles?: number | null
}

export function DistanceCard({ distanceMiles }: DistanceCardProps) {
  // Hide card if distance is 0, undefined, or null
  if (!distanceMiles || distanceMiles === 0) {
    return null
  }

  return (
    <div className="bg-[#F7F8FA] rounded-xl p-3">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
          <MapPin className="w-4 h-4 text-[#1877F2]" />
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-sm mb-0.5">Distance</h3>
          <p className="text-xs text-[#65676B]">
            {distanceMiles.toFixed(1)} miles
          </p>
        </div>
      </div>
    </div>
  )
}

