import { Car } from 'lucide-react'

interface SocialProofBadgeProps {
  neravaSessionsCount?: number
  activeDriversCount?: number
}

/**
 * Social proof badge showing session count and active drivers.
 * Only renders if data is available (hides if undefined/null/0).
 */
export function SocialProofBadge({ neravaSessionsCount, activeDriversCount }: SocialProofBadgeProps) {
  // Don't render if no data available
  if ((!neravaSessionsCount || neravaSessionsCount === 0) && (!activeDriversCount || activeDriversCount === 0)) {
    return null
  }

  return (
    <div className="flex flex-col gap-1.5">
      {neravaSessionsCount && neravaSessionsCount > 0 && (
        <div className="flex items-center gap-1.5 text-sm text-[#050505]">
          <Car className="w-4 h-4 text-[#1877F2]" />
          <span className="font-medium">{neravaSessionsCount} drivers visited</span>
        </div>
      )}
      {activeDriversCount && activeDriversCount > 0 && (
        <div className="flex items-center gap-1.5 text-xs text-green-600">
          <div className="w-1.5 h-1.5 bg-green-600 rounded-full animate-pulse" />
          <span className="font-medium">{activeDriversCount} here now</span>
        </div>
      )}
    </div>
  )
}
