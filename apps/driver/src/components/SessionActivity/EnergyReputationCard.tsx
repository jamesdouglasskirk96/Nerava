import { BatteryCharging } from 'lucide-react'
import type { EnergyReputation } from '../../services/api'

interface EnergyReputationCardProps {
  reputation: EnergyReputation
}

export function EnergyReputationCard({ reputation }: EnergyReputationCardProps) {
  const {
    points,
    tier,
    tier_color,
    next_tier,
    points_to_next,
    progress_to_next,
    streak_days,
  } = reputation

  return (
    <div className="mx-4 mt-4 bg-[#F7F8FA] rounded-card border border-[#E4E6EB] p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <BatteryCharging className="w-4 h-4 text-[#656A6B]" />
          <span className="text-sm font-semibold text-[#050505]">Energy Reputation</span>
        </div>
        {streak_days > 0 && (
          <span
            className="px-2.5 py-0.5 rounded-full text-xs font-medium"
            style={{ backgroundColor: `${tier_color}15`, color: tier_color }}
          >
            {streak_days}-day streak
          </span>
        )}
      </div>

      {/* Tier + Points */}
      <div className="flex items-baseline gap-2 mb-3">
        <span className="text-lg font-bold" style={{ color: tier_color }}>
          {tier}
        </span>
        <span className="text-sm text-[#656A6B]">{points} pts</span>
      </div>

      {/* Progress Bar */}
      {next_tier && points_to_next != null && (
        <div className="mb-2">
          <div className="h-2 bg-[#E4E6EB] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(progress_to_next * 100, 100)}%`,
                backgroundColor: tier_color,
              }}
            />
          </div>
          <p className="text-xs text-[#656A6B] mt-1">
            {points_to_next} pts to {next_tier}
          </p>
        </div>
      )}

      {/* Max tier state */}
      {!next_tier && (
        <div className="mb-2">
          <div className="h-2 bg-[#E4E6EB] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: '100%', backgroundColor: tier_color }}
            />
          </div>
          <p className="text-xs text-[#656A6B] mt-1">Max tier reached</p>
        </div>
      )}

      {/* Tagline */}
      <p className="text-xs text-[#656A6B]">Your impact & smart-charge consistency</p>
    </div>
  )
}
