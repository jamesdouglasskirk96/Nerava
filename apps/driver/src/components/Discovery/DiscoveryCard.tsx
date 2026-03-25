import { Heart } from 'lucide-react'
import type { DiscoveryItem } from './discovery-types'
import {
  distanceToMiles,
  distanceToWalkTime,
  formatReward,
  getCategoryLabel,
} from './discovery-types'
import type { ChargerSummary } from '../../types'

interface DiscoveryCardProps {
  item: DiscoveryItem
  isSelected: boolean
  onSelect: () => void
  isFavorite: boolean
  onToggleFavorite: () => void
  isActiveCharger?: boolean
}

export function DiscoveryCard({
  item,
  isSelected,
  onSelect,
  isFavorite,
  onToggleFavorite,
  isActiveCharger,
}: DiscoveryCardProps) {
  const { type, data } = item

  // Compute display fields from backend types
  const name = data.name
  const subtitle =
    type === 'charger' ? (data.network_name || 'Charging Station') : getCategoryLabel(data.types || [])
  const distancePill =
    type === 'charger' ? distanceToMiles(data.distance_m) : distanceToWalkTime(data.distance_m)
  const rewardPill =
    type === 'charger' && data.campaign_reward_cents && data.campaign_reward_cents > 0
      ? formatReward(data.campaign_reward_cents)
      : null
  const photoUrl =
    type === 'merchant' ? data.photo_url : null

  // Charger-specific display
  const chargerData = type === 'charger' ? (data as ChargerSummary) : null
  const powerLabel = chargerData?.power_kw
    ? chargerData.power_kw > 50 ? 'DC Fast' : 'Level 2'
    : null
  const powerColor = chargerData?.network_name?.toLowerCase().includes('tesla')
    ? 'bg-red-50 text-red-700'
    : chargerData?.power_kw && chargerData.power_kw > 50
      ? 'bg-blue-50 text-[#1877F2]'
      : 'bg-emerald-50 text-emerald-700'

  // Network logo for chargers
  const chargerImage =
    type === 'charger' && data.network_name?.toLowerCase().includes('tesla')
      ? '/tesla-logo.svg'
      : '/bolt-blue.svg'

  const imageUrl = type === 'merchant' ? photoUrl : chargerImage

  return (
    <div
      onClick={onSelect}
      className={`flex items-center gap-3 py-3 px-4 cursor-pointer transition-all active:scale-[0.98] ${
        isSelected
          ? 'bg-[rgba(24,119,242,0.04)] border-l-[3px] border-l-[#1877F2]'
          : 'bg-white border-l-[3px] border-l-transparent'
      }`}
      style={{
        borderBottom: '0.5px solid #E4E6EB',
      }}
    >
      {/* Thumbnail */}
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={name}
          className="w-14 h-14 rounded-xl object-cover flex-shrink-0 bg-[#F7F8FA]"
          onError={(e) => {
            ;(e.target as HTMLImageElement).src = '/bolt-blue.svg'
          }}
        />
      ) : (
        <div className="w-14 h-14 rounded-xl bg-[#F7F8FA] flex items-center justify-center flex-shrink-0">
          <span className="text-2xl">{type === 'charger' ? '⚡' : '🏪'}</span>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="text-[16px] font-semibold text-[#050505] truncate">{name}</h3>
          {isActiveCharger && (
            <span className="flex-shrink-0 px-2 py-0.5 text-[10px] font-semibold rounded-full bg-green-100 text-green-700 flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
              You're here
            </span>
          )}
        </div>
        <p className="text-[14px] text-[#656A6B] truncate">{subtitle}</p>

        {/* Pills — keep to max 3 for visual clarity */}
        <div className="flex gap-1.5 mt-1">
          <span className="px-2 py-0.5 text-xs rounded-full bg-[#E7F3FF] text-[#1877F2]">
            {distancePill}
          </span>
          {powerLabel && (
            <span className={`px-2 py-0.5 text-xs rounded-full ${powerColor}`}>
              {powerLabel}
            </span>
          )}
          {rewardPill && (
            <span className="px-2 py-0.5 text-xs rounded-full bg-[#E8F5E9] text-[#2E7D32]">
              {rewardPill}
            </span>
          )}
        </div>
      </div>

      {/* Heart Icon */}
      <button
        onClick={(e) => {
          e.stopPropagation()
          onToggleFavorite()
        }}
        className="p-2 hover:bg-[#F7F8FA] rounded-full transition-colors flex-shrink-0"
      >
        <Heart
          className={`w-5 h-5 ${isFavorite ? 'text-red-500 fill-red-500' : 'text-[#656A6B]'}`}
        />
      </button>
    </div>
  )
}
