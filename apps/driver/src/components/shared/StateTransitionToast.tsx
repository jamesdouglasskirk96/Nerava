// Toast component for state transitions (PRE_CHARGING → CHARGING_ACTIVE)
import { useEffect, useState } from 'react'
import { Zap } from 'lucide-react'

interface StateTransitionToastProps {
  show: boolean
  onHide: () => void
}

export function StateTransitionToast({ show, onHide }: StateTransitionToastProps) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    if (show) {
      setIsVisible(true)
      const timer = setTimeout(() => {
        setIsVisible(false)
        setTimeout(onHide, 300) // Wait for fade animation
      }, 3000) // Auto-hide after 3 seconds
      return () => clearTimeout(timer)
    }
  }, [show, onHide])

  if (!show && !isVisible) return null

  return (
    <div
      className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 transition-all duration-300 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'
      }`}
    >
      <div className="bg-[#1877F2] text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 max-w-sm mx-4">
        <Zap className="w-4 h-4 flex-shrink-0" />
        <p className="text-sm font-medium">
          You're near a charger — here's what's within walking distance.
        </p>
      </div>
    </div>
  )
}


