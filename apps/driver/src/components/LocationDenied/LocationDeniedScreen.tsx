// Location Denied Recovery Screen
import { MapPin, AlertCircle } from 'lucide-react'
import { Button } from '../shared/Button'
import { Zap } from 'lucide-react'

interface LocationDeniedScreenProps {
  onTryAgain: () => void
  onBrowseChargers: () => void
}

export function LocationDeniedScreen({ onTryAgain, onBrowseChargers }: LocationDeniedScreenProps) {
  return (
    <div className="min-h-screen bg-white text-[#050505] max-w-md mx-auto flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-[#E4E6EB] flex-shrink-0 px-5 py-3">
        <div className="flex items-center gap-1.5">
          <span className="tracking-tight text-[#050505]">NERAVA</span>
          <Zap className="w-4 h-4 fill-[#1877F2] text-[#1877F2]" />
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <div className="text-center space-y-6">
          {/* Icon */}
          <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>

          {/* Title */}
          <h1 className="text-2xl sm:text-3xl font-medium text-[#050505]">
            Location required
          </h1>

          {/* Description */}
          <p className="text-base text-[#65676B] leading-relaxed">
            Location is required to detect chargers near you. We use your location to show places within walking distance.
          </p>

          {/* Action Buttons */}
          <div className="pt-4 space-y-3">
            <Button onClick={onTryAgain} className="w-full">
              Try again
            </Button>
            <Button
              variant="secondary"
              onClick={onBrowseChargers}
              className="w-full flex items-center justify-center gap-2"
            >
              <MapPin className="w-4 h-4" />
              Browse chargers
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}


