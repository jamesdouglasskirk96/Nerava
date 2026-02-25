interface ActiveSessionBannerProps {
  durationMinutes: number
  kwhDelivered: number | null
  onTap: () => void
}

export function ActiveSessionBanner({ durationMinutes, kwhDelivered, onTap }: ActiveSessionBannerProps) {
  return (
    <button
      onClick={onTap}
      className="w-full bg-green-600 text-white px-4 py-3 flex items-center justify-between flex-shrink-0"
    >
      <div className="flex items-center gap-2">
        {/* Pulsing dot */}
        <span className="relative flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-300 opacity-75" />
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-white" />
        </span>
        <span className="font-medium text-sm">
          Charging
          {durationMinutes > 0 ? ` \u2022 ${durationMinutes} min` : ''}
          {kwhDelivered != null ? ` \u2022 ${kwhDelivered.toFixed(1)} kWh` : ''}
        </span>
      </div>
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
      </svg>
    </button>
  )
}
