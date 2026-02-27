interface ActiveSessionBannerProps {
  durationMinutes: number
  kwhDelivered: number | null
  onTap: () => void
  merchantName?: string
}

export function ActiveSessionBanner({ durationMinutes, kwhDelivered, onTap, merchantName }: ActiveSessionBannerProps) {
  const timeLabel = durationMinutes > 0 ? `${durationMinutes} min` : 'Just started'

  return (
    <button
      onClick={onTap}
      className="w-full bg-[#1877F2] text-white px-4 py-2.5 flex items-center justify-between flex-shrink-0"
    >
      <div className="flex items-center gap-2">
        {/* Pulsing charging dot */}
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-white" />
        </span>
        <span className="font-medium text-sm">
          {merchantName || 'Charging'}
        </span>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-sm font-medium">
          {timeLabel}
          {kwhDelivered != null ? ` · ${kwhDelivered.toFixed(1)} kWh` : ''}
        </span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </button>
  )
}
