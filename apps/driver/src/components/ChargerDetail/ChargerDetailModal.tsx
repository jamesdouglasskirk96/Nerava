import { useEffect, useState } from 'react'
import { ArrowLeft, Share2, Zap, MapPin, Navigation, Heart, DollarSign, Shield, Users } from 'lucide-react'
import { useChargerDetail, getStreetViewUrl, toggleChargerFavorite } from '../../services/api'
import { capture, DRIVER_EVENTS } from '../../analytics'
import { openExternalUrl } from '../../utils/openExternal'

interface ChargerDetailModalProps {
  chargerId: string
  chargerName: string
  networkName?: string
  lat?: number
  lng?: number
  userLat?: number
  userLng?: number
  onClose: () => void
  onMerchantSelect: (placeId: string, photoUrl?: string) => void
  isCharging: boolean
  onViewSession?: () => void
  isFavorite?: boolean
  onToggleFavorite?: () => void
}

const NETWORK_COLORS: Record<string, string> = {
  Tesla: 'from-red-600 to-red-800',
  ChargePoint: 'from-green-600 to-green-800',
  'Electrify America': 'from-green-500 to-blue-700',
  EVgo: 'from-blue-600 to-blue-800',
  Blink: 'from-teal-500 to-teal-700',
}

function getNetworkGradient(network?: string | null): string {
  if (network && NETWORK_COLORS[network]) return NETWORK_COLORS[network]
  return 'from-[#1877F2] to-[#0D5BC6]'
}

function formatDistance(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)}m`
  return `${(meters / 1609.34).toFixed(1)} mi`
}

function getScoreLabel(score: number): { label: string; color: string; bg: string } {
  if (score >= 80) return { label: 'Excellent', color: 'text-green-700', bg: 'bg-green-50 border-green-200' }
  if (score >= 60) return { label: 'Good', color: 'text-yellow-700', bg: 'bg-yellow-50 border-yellow-200' }
  if (score >= 40) return { label: 'Fair', color: 'text-orange-700', bg: 'bg-orange-50 border-orange-200' }
  return { label: 'Poor', color: 'text-red-700', bg: 'bg-red-50 border-red-200' }
}

export function ChargerDetailModal({
  chargerId,
  chargerName,
  networkName,
  lat,
  lng,
  userLat,
  userLng,
  onClose,
  onMerchantSelect,
  isCharging,
  onViewSession,
  isFavorite: isFavoriteProp,
  onToggleFavorite,
}: ChargerDetailModalProps) {
  const { data: detail, isLoading } = useChargerDetail(chargerId, userLat, userLng)
  const [streetViewUrl, setStreetViewUrl] = useState<string | null>(null)
  const [streetViewError, setStreetViewError] = useState(false)
  const [localFavorite, setLocalFavorite] = useState(isFavoriteProp ?? false)

  useEffect(() => {
    capture(DRIVER_EVENTS.CHARGER_DETAIL_VIEWED, {
      charger_id: chargerId,
      charger_name: chargerName,
      network: networkName,
    })
  }, [chargerId, chargerName, networkName])

  // Load Street View URL
  useEffect(() => {
    const url = getStreetViewUrl(chargerId)
    setStreetViewUrl(url)
  }, [chargerId])

  const gradient = getNetworkGradient(detail?.network_name ?? networkName)
  const connectors = detail?.connector_types ?? []
  const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

  const handleGetDirections = () => {
    const destLat = detail?.lat ?? lat
    const destLng = detail?.lng ?? lng
    capture(DRIVER_EVENTS.CHARGER_DIRECTIONS_CLICKED, {
      charger_id: chargerId,
      charger_name: chargerName,
    })
    if (destLat && destLng) {
      openExternalUrl(`https://www.google.com/maps/dir/?api=1&destination=${destLat},${destLng}`)
    }
  }

  const handleShare = async () => {
    const url = `https://app.nerava.network/charger/${chargerId}`
    const shareData = { title: chargerName, text: `Check out ${chargerName} on Nerava!`, url }
    if (navigator.share && navigator.canShare?.(shareData)) {
      try { await navigator.share(shareData); return } catch { /* cancelled */ }
    }
    try { await navigator.clipboard.writeText(url) } catch { /* ignore */ }
  }

  const handleToggleFavorite = async () => {
    setLocalFavorite(!localFavorite)
    onToggleFavorite?.()
    try {
      await toggleChargerFavorite(chargerId, localFavorite)
    } catch {
      setLocalFavorite(localFavorite) // revert
    }
  }

  // Pricing display
  const pricing = detail?.pricing_per_kwh
  const rewardPerSession = detail?.active_reward_cents ? detail.active_reward_cents / 100 : 0

  return (
    <div className="fixed inset-0 bg-[#242526] z-[3000]">
      <div className="h-screen w-full bg-white flex flex-col overflow-hidden" style={{ height: 'var(--app-height, 100dvh)' }}>
        {/* Hero — Street View or gradient */}
        <div className={`relative h-44 flex-shrink-0 ${!streetViewUrl || streetViewError ? `bg-gradient-to-br ${gradient}` : ''}`}>
          {streetViewUrl && !streetViewError ? (
            <img
              src={streetViewUrl}
              alt={chargerName}
              className="w-full h-full object-cover"
              onError={() => setStreetViewError(true)}
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <Zap className="w-16 h-16 text-white/30" />
            </div>
          )}

          <button
            onClick={onClose}
            className="absolute top-4 left-4 w-11 h-11 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-white/30 active:scale-95 transition-all"
            aria-label="Go back"
          >
            <ArrowLeft className="w-5 h-5 text-white" />
          </button>

          <div className="absolute top-4 right-4 flex gap-2">
            <button
              onClick={handleToggleFavorite}
              className="w-11 h-11 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-white/30 active:scale-95 transition-all"
              aria-label={localFavorite ? 'Remove from favorites' : 'Add to favorites'}
            >
              <Heart className={`w-5 h-5 ${localFavorite ? 'text-red-500 fill-red-500' : 'text-white'}`} />
            </button>
            <button
              onClick={handleShare}
              className="w-11 h-11 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-white/30 active:scale-95 transition-all"
              aria-label="Share charger"
            >
              <Share2 className="w-5 h-5 text-white" />
            </button>
          </div>

          {/* Network badge */}
          <div className="absolute bottom-4 left-4">
            <span className="px-3 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm text-white font-medium">
              {detail?.network_name ?? networkName ?? 'Charging Station'}
            </span>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="px-6 py-5">
            {/* Title + Live Drivers */}
            <h1 className="text-2xl font-semibold mb-1 text-[#050505]">{detail?.name ?? chargerName}</h1>
            <p className="text-sm text-[#65676B] mb-1">
              {detail?.network_name ?? networkName}
              {connectors.length > 0 && ` · ${connectors.join(', ')}`}
            </p>

            {/* Live drivers indicator */}
            {detail && detail.drivers_charging_now > 0 && (
              <div className="flex items-center gap-1.5 mb-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
                </span>
                <span className="text-xs font-medium text-green-700">
                  {detail.drivers_charging_now} Nerava driver{detail.drivers_charging_now !== 1 ? 's' : ''} charging now
                </span>
              </div>
            )}

            {/* Reward + Nerava Score badges */}
            <div className="flex flex-wrap gap-2 mb-3 mt-1">
              {detail?.active_reward_cents != null && detail.active_reward_cents > 0 && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-green-50 border border-green-200 rounded-full text-xs font-medium text-green-700">
                  Earn ${(detail.active_reward_cents / 100).toFixed(2)} per session
                </span>
              )}
              {detail?.nerava_score != null && (
                <span className={`inline-flex items-center gap-1 px-2.5 py-1 border rounded-full text-xs font-medium ${getScoreLabel(detail.nerava_score).bg} ${getScoreLabel(detail.nerava_score).color}`}>
                  <Shield className="w-3 h-3" />
                  {getScoreLabel(detail.nerava_score).label} ({Math.round(detail.nerava_score)})
                </span>
              )}
            </div>

            {/* Loading skeleton */}
            {isLoading ? (
              <div className="space-y-3 mt-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-[#F7F8FA] rounded-2xl p-3 animate-pulse h-16" />
                ))}
              </div>
            ) : (
              <div className="space-y-3 mt-3">
                {/* Pricing card */}
                {(pricing != null || detail?.active_reward_cents) && (
                  <div className="bg-[#F7F8FA] rounded-2xl p-3">
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <DollarSign className="w-4 h-4 text-green-600" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-sm mb-0.5">Pricing</h3>
                        {pricing != null ? (
                          <div>
                            <p className="text-xs text-[#65676B]">
                              ${pricing.toFixed(2)}/kWh
                              {detail?.pricing_source === 'network_average' && ' (network avg)'}
                            </p>
                            {rewardPerSession > 0 && (
                              <p className="text-xs text-green-600 font-medium mt-0.5">
                                Net cost after reward: ~${Math.max(0, pricing - (rewardPerSession / 30)).toFixed(2)}/kWh
                              </p>
                            )}
                          </div>
                        ) : (
                          <p className="text-xs text-[#65676B]">Pricing varies — check station</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Stalls & Power card */}
                {(detail?.num_evse || detail?.power_kw) && (
                  <div className="bg-[#F7F8FA] rounded-2xl p-3">
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                        <Zap className="w-4 h-4 text-[#1877F2]" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-sm mb-0.5">Stalls & Power</h3>
                        <p className="text-xs text-[#65676B]">
                          {detail?.num_evse ? `${detail.num_evse} stalls` : ''}
                          {detail?.num_evse && detail?.power_kw ? ' · ' : ''}
                          {detail?.power_kw ? `${detail.power_kw} kW` : ''}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Distance card */}
                <div className="bg-[#F7F8FA] rounded-2xl p-3">
                  <div className="flex items-start gap-3">
                    <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                      <Navigation className="w-4 h-4 text-[#1877F2]" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-sm mb-0.5">Distance</h3>
                      <p className="text-xs text-[#65676B]">
                        {detail ? `${formatDistance(detail.distance_m)} · ${detail.drive_time_min} min drive` : '...'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Address card */}
                {detail?.address && (
                  <div className="bg-[#F7F8FA] rounded-2xl p-3">
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
                        <MapPin className="w-4 h-4 text-[#1877F2]" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-sm mb-0.5">Address</h3>
                        <p className="text-xs text-[#65676B]">
                          {detail.address}
                          {detail.city && `, ${detail.city}`}
                          {detail.state && `, ${detail.state}`}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Connector pills */}
                {connectors.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {connectors.map((c) => (
                      <span key={c} className="px-3 py-1.5 bg-[#F7F8FA] border border-[#E4E6EB] rounded-full text-xs font-medium text-[#050505]">
                        {c}
                      </span>
                    ))}
                  </div>
                )}

                {/* Community stats */}
                {detail && detail.total_sessions_30d > 0 && (
                  <div className="bg-[#F7F8FA] rounded-2xl p-3">
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <Users className="w-4 h-4 text-purple-600" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-medium text-sm mb-0.5">Community</h3>
                        <p className="text-xs text-[#65676B]">
                          {detail.total_sessions_30d} session{detail.total_sessions_30d !== 1 ? 's' : ''} this month
                          {' · '}
                          {detail.unique_drivers_30d} driver{detail.unique_drivers_30d !== 1 ? 's' : ''}
                          {detail.avg_duration_min > 0 && ` · avg ${detail.avg_duration_min} min`}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Nearby merchants */}
                {detail && detail.nearby_merchants.length > 0 && (
                  <div className="mt-2">
                    <h3 className="font-medium text-sm mb-3">Nearby while you charge</h3>
                    <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-hide">
                      {detail.nearby_merchants.map((m) => {
                        const photoSrc = m.photo_url.startsWith('/static') ? `${API_BASE}${m.photo_url}` : m.photo_url
                        return (
                          <button
                            key={m.place_id}
                            onClick={() => {
                              capture(DRIVER_EVENTS.CHARGER_MERCHANT_CLICKED, {
                                charger_id: chargerId,
                                merchant_place_id: m.place_id,
                                merchant_name: m.name,
                              })
                              onMerchantSelect(m.place_id, m.photo_url)
                            }}
                            className="flex-shrink-0 w-32 text-left active:scale-[0.97] transition-transform"
                          >
                            <div className="relative w-32 h-24 rounded-xl overflow-hidden mb-1.5 bg-[#E4E6EB]">
                              <img src={photoSrc} alt={m.name} className="w-full h-full object-cover" loading="lazy" />
                              {m.has_exclusive && (
                                <span className="absolute top-1.5 right-1.5 px-1.5 py-0.5 bg-yellow-500/90 rounded text-[10px] font-medium text-white">
                                  Exclusive
                                </span>
                              )}
                            </div>
                            <p className="text-xs font-medium text-[#050505] truncate">{m.name}</p>
                            <p className="text-[10px] text-[#65676B]">{m.walk_time_min} min walk</p>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Fixed CTAs */}
        <div className="flex-shrink-0 px-6 py-4 bg-white border-t border-gray-100" style={{ paddingBottom: 'calc(env(safe-area-inset-bottom, 0px) + 1rem)' }}>
          <div className="flex flex-col gap-3">
            <button
              onClick={handleGetDirections}
              className="w-full py-3.5 bg-white border-2 border-[#1877F2] text-[#1877F2] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-[0.98] transition-all"
            >
              Get Directions
            </button>
            {isCharging && onViewSession && (
              <button
                onClick={onViewSession}
                className="w-full py-3.5 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-[0.98] transition-all"
              >
                View Charging Session
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
