import { Leaf, Zap, Trophy, DollarSign } from 'lucide-react'
import { useAccountStats } from '../../services/api'

export function AccountStatsCard() {
  const { data: stats, isLoading } = useAccountStats()

  if (isLoading) {
    return (
      <div className="bg-gray-50 rounded-2xl border border-[#E4E6EB] p-4 animate-pulse">
        <div className="h-20 bg-gray-200 rounded-xl" />
      </div>
    )
  }

  if (!stats || stats.total_sessions === 0) return null

  return (
    <div className="space-y-3">
      {/* CO2 Impact Card */}
      {stats.co2_avoided_kg > 0 && (
        <div className="bg-green-50 rounded-2xl p-4 border border-green-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <Leaf className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="font-semibold text-green-900">{stats.co2_avoided_kg} kg CO2 avoided</p>
              <p className="text-xs text-green-700">By charging your EV instead of gas</p>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-50 rounded-2xl p-3 border border-[#E4E6EB]">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-4 h-4 text-[#1877F2]" />
            <span className="text-xs text-[#65676B]">Sessions</span>
          </div>
          <p className="text-lg font-bold text-[#050505]">{stats.total_sessions}</p>
        </div>
        <div className="bg-gray-50 rounded-2xl p-3 border border-[#E4E6EB]">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-4 h-4 text-yellow-500" />
            <span className="text-xs text-[#65676B]">Energy</span>
          </div>
          <p className="text-lg font-bold text-[#050505]">{stats.total_kwh} kWh</p>
        </div>
        <div className="bg-gray-50 rounded-2xl p-3 border border-[#E4E6EB]">
          <div className="flex items-center gap-2 mb-1">
            <DollarSign className="w-4 h-4 text-green-500" />
            <span className="text-xs text-[#65676B]">Earned</span>
          </div>
          <p className="text-lg font-bold text-[#050505]">${(stats.total_earned_cents / 100).toFixed(2)}</p>
        </div>
        <div className="bg-gray-50 rounded-2xl p-3 border border-[#E4E6EB]">
          <div className="flex items-center gap-2 mb-1">
            <Trophy className="w-4 h-4 text-purple-500" />
            <span className="text-xs text-[#65676B]">Nova Points</span>
          </div>
          <p className="text-lg font-bold text-[#050505]">{stats.total_nova}</p>
        </div>
      </div>

      {/* Streak */}
      {stats.current_streak > 0 && (
        <div className="bg-orange-50 rounded-2xl p-3 border border-orange-200 flex items-center gap-3">
          <span className="text-2xl">🔥</span>
          <div>
            <p className="font-semibold text-orange-900">{stats.current_streak} day streak</p>
            <p className="text-xs text-orange-700">Keep charging to maintain your streak</p>
          </div>
        </div>
      )}
    </div>
  )
}
