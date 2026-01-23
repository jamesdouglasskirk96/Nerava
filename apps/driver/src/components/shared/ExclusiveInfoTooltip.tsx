// Tooltip component explaining "Exclusive" terminology
import { useState } from 'react'
import { Info } from 'lucide-react'

interface ExclusiveInfoTooltipProps {
  className?: string
}

export function ExclusiveInfoTooltip({ className = '' }: ExclusiveInfoTooltipProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        type="button"
        onClick={() => setShowTooltip(!showTooltip)}
        onBlur={() => setShowTooltip(false)}
        className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-[#1877F2]/10 text-[#1877F2] hover:bg-[#1877F2]/20 transition-colors"
        aria-label="What is Exclusive?"
      >
        <Info className="w-3 h-3" />
      </button>
      
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-3 bg-[#050505] text-white text-xs rounded-lg shadow-lg z-50">
          <p className="leading-relaxed">
            Exclusive = a special offer for Nerava users, redeemable during your charging session.
          </p>
          {/* Arrow */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="w-2 h-2 bg-[#050505] rotate-45"></div>
          </div>
        </div>
      )}
    </div>
  )
}


