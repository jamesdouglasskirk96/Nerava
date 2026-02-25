import { Zap } from 'lucide-react'
import { useChargingSessions, useTeslaStatus } from '../../services/api'
import { SessionCard } from './SessionCard'

interface SessionActivityScreenProps {
  onClose: () => void
  isActive?: boolean
  durationMinutes?: number
  kwhDelivered?: number | null
}

export function SessionActivityScreen({
  onClose,
  isActive,
  durationMinutes,
  kwhDelivered,
}: SessionActivityScreenProps) {
  const { data: teslaStatus, isLoading: teslaLoading } = useTeslaStatus()
  const { data: sessionsData, isLoading: sessionsLoading, error: sessionsError, refetch } = useChargingSessions(50)

  const sessions = sessionsData?.sessions || []
  const isTeslaConnected = teslaStatus?.connected === true

  // Compute stats
  const totalSessions = sessions.length
  const totalKwh = sessions.reduce((sum, s) => sum + (s.kwh_delivered || 0), 0)
  const totalEarned = sessions.reduce((sum, s) => sum + (s.incentive?.amount_cents || 0), 0)

  const isLoading = teslaLoading || sessionsLoading

  return (
    <div className="fixed inset-0 bg-white z-50 flex flex-col" style={{ height: 'var(--app-height, 100dvh)' }}>
      {/* Header */}
      <header className="bg-white border-b border-[#E4E6EB] flex-shrink-0 px-4 py-3 flex items-center">
        <button
          onClick={onClose}
          className="flex items-center text-[#050505]"
        >
          <svg className="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>
        <h1 className="flex-1 text-center font-semibold text-[#050505]">Charging Activity</h1>
        <div className="w-14" /> {/* Spacer for centering */}
      </header>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto" style={{ paddingBottom: 'calc(1rem + env(safe-area-inset-bottom, 0px))' }}>
        {/* Active Session Card */}
        {isActive && (
          <div className="mx-4 mt-4 p-4 bg-green-50 border border-green-200 rounded-card">
            <div className="flex items-center gap-2 mb-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
              </span>
              <span className="text-sm font-semibold text-green-800">Charging Now</span>
            </div>
            <div className="flex items-center gap-4 text-sm text-green-700">
              {(durationMinutes ?? 0) > 0 && <span>{durationMinutes} min</span>}
              {kwhDelivered != null && <span>{kwhDelivered.toFixed(1)} kWh</span>}
            </div>
          </div>
        )}

        {/* Stats Row */}
        {!isLoading && isTeslaConnected && sessions.length > 0 && (
          <div className="grid grid-cols-3 gap-3 mx-4 mt-4">
            <div className="bg-[#F7F8FA] rounded-card p-3 text-center">
              <p className="text-lg font-bold text-[#050505]">{totalSessions}</p>
              <p className="text-xs text-[#656A6B]">Sessions</p>
            </div>
            <div className="bg-[#F7F8FA] rounded-card p-3 text-center">
              <p className="text-lg font-bold text-[#050505]">{totalKwh.toFixed(1)}</p>
              <p className="text-xs text-[#656A6B]">kWh</p>
            </div>
            <div className="bg-[#F7F8FA] rounded-card p-3 text-center">
              <p className="text-lg font-bold text-green-600">${(totalEarned / 100).toFixed(2)}</p>
              <p className="text-xs text-[#656A6B]">Earned</p>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="px-4 mt-4 space-y-3">
          {isLoading ? (
            // Loading skeleton
            <>
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-[#F7F8FA] rounded-card border border-[#E4E6EB] p-4 animate-pulse">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gray-200" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-1/3" />
                      <div className="h-3 bg-gray-200 rounded w-1/4" />
                    </div>
                  </div>
                </div>
              ))}
            </>
          ) : sessionsError ? (
            // Error state
            <div className="text-center py-12">
              <p className="text-[#656A6B] mb-4">Failed to load sessions.</p>
              <button
                onClick={() => refetch()}
                className="px-6 py-2.5 bg-[#1877F2] text-white text-sm font-medium rounded-full hover:bg-[#166FE5] active:scale-[0.98] transition-all"
              >
                Retry
              </button>
            </div>
          ) : !isTeslaConnected ? (
            // No Tesla connected
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-16 h-16 bg-[#F7F8FA] rounded-full flex items-center justify-center mb-4">
                <Zap className="w-8 h-8 text-[#656A6B]" />
              </div>
              <h3 className="text-lg font-medium text-[#050505] mb-1">Connect your Tesla</h3>
              <p className="text-sm text-[#656A6B] max-w-[260px]">
                Link your Tesla account to automatically track charging sessions and earn rewards.
              </p>
            </div>
          ) : sessions.length === 0 ? (
            // Empty state (Tesla connected, no sessions)
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-16 h-16 bg-[#F7F8FA] rounded-full flex items-center justify-center mb-4">
                <Zap className="w-8 h-8 text-[#656A6B]" />
              </div>
              <h3 className="text-lg font-medium text-[#050505] mb-1">No sessions yet</h3>
              <p className="text-sm text-[#656A6B] max-w-[260px]">
                Your charging sessions will appear here once we detect charging from your Tesla.
              </p>
            </div>
          ) : (
            // Session list
            sessions.map((session) => (
              <SessionCard key={session.id} session={session} />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
