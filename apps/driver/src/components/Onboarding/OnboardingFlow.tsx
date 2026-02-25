// Onboarding Flow — location permission screen only
// Informational slides removed; Tesla login replaces the "what is Nerava" flow.
import { Button } from '../shared/Button'
import { Zap } from 'lucide-react'

interface OnboardingFlowProps {
  onComplete: () => void
  onRequestLocation: () => void
  onSkipLocation: () => void
}

export function OnboardingFlow({ onComplete, onRequestLocation, onSkipLocation }: OnboardingFlowProps) {
  const handleEnableLocation = () => {
    onRequestLocation()
    onComplete()
  }

  const handleNotNow = () => {
    onSkipLocation()
    onComplete()
  }

  return (
    <div className="bg-white text-[#050505] max-w-md mx-auto flex flex-col" style={{ height: 'var(--app-height, 100dvh)' }}>
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
          <h1 className="text-2xl sm:text-3xl font-medium text-[#050505]">
            Location powers it
          </h1>
          <p className="text-base text-[#65676B] leading-relaxed">
            We use your location to detect chargers and show places within walking distance.
          </p>
          <div className="pt-4 space-y-3">
            <Button onClick={handleEnableLocation} className="w-full">
              Enable location
            </Button>
            <Button
              variant="secondary"
              onClick={handleNotNow}
              className="w-full"
            >
              Not now
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
