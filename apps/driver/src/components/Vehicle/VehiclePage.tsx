import { useState, useEffect } from 'react'
import { Zap, Battery, BatteryCharging, Pencil, Check, X } from 'lucide-react'
import { useTeslaStatus, useChargingSessions, useEnergyReputation } from '../../services/api'
import { getCleanModelName } from '../shared/TeslaSilhouette'
import { SessionCard } from '../SessionActivity/SessionCard'
import { EnergyReputationCard } from '../SessionActivity/EnergyReputationCard'

const VEHICLE_NICKNAME_KEY = 'nerava_vehicle_nickname'

interface VehiclePageProps {
  onClose: () => void
  isCharging?: boolean
  durationMinutes?: number
  kwhDelivered?: number | null
  minutesToFull?: number | null
}

function getBatteryColor(level: number): string {
  if (level >= 60) return '#10B981' // green
  if (level >= 30) return '#F59E0B' // amber
  return '#EF4444' // red
}

export function VehiclePage({ onClose, isCharging, durationMinutes, kwhDelivered, minutesToFull }: VehiclePageProps) {
  const { data: tesla, isLoading: teslaLoading } = useTeslaStatus()
  const { data: sessionsData, isLoading: sessionsLoading } = useChargingSessions(50)
  const { data: reputation } = useEnergyReputation()

  const sessions = sessionsData?.sessions || []
  const batteryLevel = tesla?.battery_level ?? null
  const modelName = getCleanModelName(tesla?.vehicle_model ?? undefined)
  const isConnected = tesla?.connected === true

  const totalSessions = sessions.length
  const totalKwh = sessions.reduce((sum, s) => sum + (s.kwh_delivered || 0), 0)
  const totalEarned = sessions.reduce((sum, s) => sum + (s.incentive?.amount_cents || 0), 0)

  // Nickname state
  const [nickname, setNickname] = useState(() => localStorage.getItem(VEHICLE_NICKNAME_KEY) || '')
  const [editingNickname, setEditingNickname] = useState(false)
  const [nicknameInput, setNicknameInput] = useState('')

  // Default nickname from Tesla API or fallback
  useEffect(() => {
    if (!nickname && tesla?.vehicle_name) {
      setNickname(tesla.vehicle_name)
      localStorage.setItem(VEHICLE_NICKNAME_KEY, tesla.vehicle_name)
    }
  }, [tesla?.vehicle_name, nickname])

  const displayNickname = nickname || tesla?.vehicle_name || 'My Tesla'

  const handleStartEditNickname = () => {
    setNicknameInput(displayNickname)
    setEditingNickname(true)
  }

  const handleSaveNickname = () => {
    const trimmed = nicknameInput.trim()
    if (trimmed) {
      setNickname(trimmed)
      localStorage.setItem(VEHICLE_NICKNAME_KEY, trimmed)
    }
    setEditingNickname(false)
  }

  const handleCancelNickname = () => {
    setEditingNickname(false)
  }

  return (
    <div className="fixed inset-0 bg-white z-[3000] flex flex-col" style={{ height: 'var(--app-height, 100dvh)' }}>
      {/* Header */}
      <header className="bg-white border-b border-gray-100 flex-shrink-0 px-4 py-3 flex items-center">
        <button onClick={onClose} className="flex items-center text-[#050505]">
          <svg className="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>
        <h1 className="flex-1 text-center font-semibold text-[#050505]">My Vehicle</h1>
        <div className="w-14" />
      </header>

      <div className="flex-1 overflow-y-auto" style={{ paddingBottom: 'calc(1rem + env(safe-area-inset-bottom, 0px))' }}>
        {teslaLoading ? (
          <div className="mx-4 mt-6">
            <div className="bg-gray-50 rounded-2xl h-56 animate-pulse" />
          </div>
        ) : !isConnected ? (
          <div className="text-center py-16 px-6">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Battery className="w-8 h-8 text-gray-400" />
            </div>
            <p className="text-lg font-semibold text-[#050505] mb-1">No Vehicle Connected</p>
            <p className="text-sm text-[#65676B]">Connect your Tesla to see vehicle info and battery status</p>
          </div>
        ) : (
          <>
            {/* Battery Hero Card */}
            <div className="mx-4 mt-4">
              <div
                className="rounded-2xl p-5 relative overflow-hidden"
                style={{ backgroundColor: batteryLevel != null ? getBatteryColor(batteryLevel) : '#6B7280' }}
              >
                {/* Background pattern */}
                <div className="absolute inset-0 opacity-10">
                  <div className="absolute right-0 top-0 w-32 h-32 rounded-full bg-white/20 -translate-y-8 translate-x-8" />
                  <div className="absolute left-0 bottom-0 w-24 h-24 rounded-full bg-white/10 translate-y-6 -translate-x-6" />
                </div>

                <div className="relative">
                  {/* Battery percentage */}
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-white/80 text-sm font-medium">Battery Level</p>
                      <p className="text-5xl font-bold text-white">
                        {batteryLevel != null ? `${batteryLevel}%` : '--'}
                      </p>
                    </div>
                    {isCharging ? (
                      <BatteryCharging className="w-10 h-10 text-white/80" />
                    ) : (
                      <Battery className="w-10 h-10 text-white/80" />
                    )}
                  </div>

                  {/* Battery bar */}
                  {batteryLevel != null && (
                    <div className="w-full h-3 bg-white/20 rounded-full overflow-hidden mb-4">
                      <div
                        className="h-full bg-white rounded-full transition-all duration-500"
                        style={{ width: `${batteryLevel}%` }}
                      />
                    </div>
                  )}

                  {/* Vehicle logo + info */}
                  <div className="flex items-end gap-4">
                    <div className="w-16 h-16 flex-shrink-0 flex items-center justify-center">
                      <img src="/tesla-t-logo.png" alt="Tesla" className="w-12 h-12 object-contain opacity-90" />
                    </div>
                    <div className="flex-1 min-w-0 pb-1">
                      {editingNickname ? (
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            value={nicknameInput}
                            onChange={(e) => setNicknameInput(e.target.value)}
                            className="flex-1 min-w-0 bg-white/20 text-white placeholder-white/50 text-[16px] font-semibold rounded-lg px-2 py-1 outline-none focus:bg-white/30"
                            placeholder="Car nickname"
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveNickname()
                              if (e.key === 'Escape') handleCancelNickname()
                            }}
                          />
                          <button onClick={handleSaveNickname} className="p-1 bg-white/20 rounded-full">
                            <Check className="w-4 h-4 text-white" />
                          </button>
                          <button onClick={handleCancelNickname} className="p-1 bg-white/20 rounded-full">
                            <X className="w-4 h-4 text-white" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <p className="text-white font-semibold text-base truncate">
                            {displayNickname}
                          </p>
                          <button onClick={handleStartEditNickname} className="p-1 bg-white/20 rounded-full flex-shrink-0">
                            <Pencil className="w-3 h-3 text-white" />
                          </button>
                        </div>
                      )}
                      <p className="text-white/70 text-xs">
                        {tesla?.exterior_color && `${tesla.exterior_color}`}
                        {tesla?.exterior_color && tesla?.vehicle_year && ' · '}
                        {tesla?.vehicle_year && `${tesla.vehicle_year}`}
                        {(tesla?.exterior_color || tesla?.vehicle_year) && modelName !== 'Tesla' && ` · ${modelName}`}
                        {!tesla?.exterior_color && !tesla?.vehicle_year && modelName}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Active Charging Session */}
            {isCharging && (
              <div className="mx-4 mt-4 rounded-2xl overflow-hidden" style={{ background: 'linear-gradient(135deg, #059669, #10B981)' }}>
                <div className="p-4">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="relative flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-white" />
                      </span>
                      <span className="text-sm font-bold text-white">Charging Active</span>
                    </div>
                    {minutesToFull != null && minutesToFull > 0 && (
                      <span className="text-sm font-semibold text-white/90">{minutesToFull} min remaining</span>
                    )}
                  </div>

                  {/* Progress bar - estimated from time */}
                  {minutesToFull != null && (durationMinutes ?? 0) > 0 && (
                    <div className="mb-3">
                      <div className="w-full h-2.5 bg-white/20 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-white rounded-full transition-all duration-1000"
                          style={{
                            width: `${Math.min(100, Math.max(5, ((durationMinutes ?? 0) / ((durationMinutes ?? 0) + minutesToFull)) * 100))}%`,
                            animation: 'pulse 2s ease-in-out infinite',
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Stats row */}
                  <div className="flex items-center gap-4">
                    {(durationMinutes ?? 0) > 0 && (
                      <div className="flex items-center gap-1.5">
                        <Zap className="w-3.5 h-3.5 text-white/70" />
                        <span className="text-sm font-medium text-white">{durationMinutes} min</span>
                      </div>
                    )}
                    {kwhDelivered != null && (
                      <div className="flex items-center gap-1.5">
                        <BatteryCharging className="w-3.5 h-3.5 text-white/70" />
                        <span className="text-sm font-medium text-white">{kwhDelivered.toFixed(1)} kWh</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Stats grid */}
            {sessions.length > 0 && (
              <div className="grid grid-cols-3 gap-3 mx-4 mt-4">
                <div className="bg-gray-50 rounded-2xl p-3 text-center">
                  <p className="text-lg font-bold text-[#050505]">{totalSessions}</p>
                  <p className="text-xs text-[#65676B]">Sessions</p>
                </div>
                <div className="bg-gray-50 rounded-2xl p-3 text-center">
                  <p className="text-lg font-bold text-[#050505]">{totalKwh.toFixed(1)}</p>
                  <p className="text-xs text-[#65676B]">kWh</p>
                </div>
                <div className="bg-gray-50 rounded-2xl p-3 text-center">
                  <p className="text-lg font-bold text-[#050505]">${(totalEarned / 100).toFixed(2)}</p>
                  <p className="text-xs text-[#65676B]">Earned</p>
                </div>
              </div>
            )}

            {/* Energy Reputation */}
            {reputation && (
              <div className="mx-4 mt-4">
                <EnergyReputationCard reputation={reputation} />
              </div>
            )}

            {/* Session History */}
            <div className="mx-4 mt-6">
              <h3 className="text-base font-semibold text-[#050505] mb-3">Session History</h3>
              {sessionsLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-gray-50 rounded-2xl h-20 animate-pulse" />
                  ))}
                </div>
              ) : sessions.length === 0 ? (
                <div className="text-center py-8">
                  <Zap className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-[#65676B]">No sessions yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {sessions.map((session) => (
                    <SessionCard key={session.id} session={session} />
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
