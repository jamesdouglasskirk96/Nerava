interface LiveStallIndicatorProps {
  availableStalls: number
  totalStalls: number
  lastUpdatedAt?: string | null // ISO timestamp string, optional
}

/**
 * Visual stall availability indicator with color-coded dots.
 * Shows up to 5 dots representing stall availability.
 * Colors: green (3+ available), yellow (1-2), red (0)
 */
export function LiveStallIndicator({ availableStalls, totalStalls, lastUpdatedAt }: LiveStallIndicatorProps) {
  // Determine color based on availability
  const getDotColor = (index: number) => {
    if (index >= availableStalls) {
      return 'bg-gray-300' // Unavailable
    }
    if (availableStalls >= 3) {
      return 'bg-green-500' // Good availability
    }
    if (availableStalls >= 1) {
      return 'bg-yellow-500' // Low availability
    }
    return 'bg-red-500' // Full
  }

  // Calculate time ago for last updated
  const getTimeAgo = (): string | null => {
    if (!lastUpdatedAt) return null
    try {
      const updated = new Date(lastUpdatedAt)
      const now = new Date()
      const diffMs = now.getTime() - updated.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      
      if (diffMins < 1) return 'Just now'
      if (diffMins === 1) return '1 min ago'
      if (diffMins < 60) return `${diffMins} min ago`
      const diffHours = Math.floor(diffMins / 60)
      if (diffHours === 1) return '1 hour ago'
      return `${diffHours} hours ago`
    } catch {
      return null
    }
  }

  const timeAgo = getTimeAgo()
  const displayStalls = Math.min(totalStalls, 5) // Show max 5 dots

  return (
    <div className="flex flex-col gap-1.5" role="status" aria-label={`${availableStalls} of ${totalStalls} stalls available`}>
      <div className="flex items-center gap-2">
        {/* Visual dots — decorative, text label below conveys availability */}
        <div className="flex gap-0.5" aria-hidden="true">
          {Array.from({ length: displayStalls }).map((_, index) => (
            <div
              key={index}
              className={`w-2 h-2 rounded-full ${getDotColor(index)}`}
            />
          ))}
        </div>
        {/* Text label */}
        <span className="text-xs text-[#65676B]">
          {availableStalls > 0 ? (
            <span className={`font-medium ${
              availableStalls >= 3 ? 'text-green-600' : 
              availableStalls >= 1 ? 'text-yellow-600' : 
              'text-red-600'
            }`}>
              {availableStalls} open now
            </span>
          ) : (
            <span className="text-red-600 font-medium">Full</span>
          )}
        </span>
      </div>
      {/* Updated timestamp - conditionally show */}
      {timeAgo && (
        <span className="text-[10px] text-[#65676B]">
          Updated {timeAgo}
        </span>
      )}
      {!timeAgo && lastUpdatedAt === undefined && (
        <span className="text-[10px] text-[#65676B] opacity-50">
          {/* TODO: Backend - add last_updated to charger response */}
        </span>
      )}
    </div>
  )
}
