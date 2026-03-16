import { useState, useEffect, useMemo, useCallback } from 'react'
import { Search, SlidersHorizontal, LocateFixed, X, Zap } from 'lucide-react'
import { DiscoveryMap } from './DiscoveryMap'
import { DiscoverySheet } from './DiscoverySheet'
import type { DiscoveryItem, SheetPosition } from './discovery-types'
import { getItemId } from './discovery-types'
import { getCleanModelName } from '../shared/TeslaSilhouette'
import type { ChargerSummary, MerchantSummary } from '../../types'

interface ActiveSessionInfo {
  sessionId: string | null
  durationMinutes: number
  kwhDelivered: number | null
  onTap: () => void
  onSessionEnded?: () => void
  chargerId?: string | null
}

interface VehicleInfo {
  connected: boolean
  name?: string
  vin?: string
  vehicleModel?: string
  vehicleYear?: number | null
  exteriorColor?: string | null
  batteryPercent?: number | null
  isCharging?: boolean
  durationMinutes?: number
  minutesToFull?: number | null
  kwhDelivered?: number | null
  onTap: () => void
  onConnect?: () => void
}

interface DiscoveryViewProps {
  chargers: ChargerSummary[]
  merchants: MerchantSummary[]
  userLat?: number
  userLng?: number
  isLoading: boolean
  hasError: boolean
  searchQuery: string
  onSearchChange: (q: string) => void
  selectedFilters: string[]
  onFilterToggle: (filter: string) => void
  onChargerSelect: (charger: ChargerSummary) => void
  onMerchantSelect: (merchantPlaceId: string, photoUrl?: string) => void
  onRefresh: () => void
  likedMerchants: string[]
  onToggleLike: (id: string) => void
  activeSession?: ActiveSessionInfo | null
  onSearchSubmit?: (query: string) => void
  onClearSearch?: () => void
  searchLocation?: { lat: number; lng: number; name: string } | null
  isSearching?: boolean
  vehicle?: VehicleInfo | null
  onSearchArea?: (lat: number, lng: number) => void
  walletBalanceCents?: number
  onWalletTap?: () => void
}

const connectorTypes = [
  { id: 'ccs', label: 'CCS' },
  { id: 'tesla', label: 'Tesla' },
  { id: 'chademo', label: 'CHAdeMO' },
  { id: 'j1772', label: 'J1772' },
  { id: 'dc_fast', label: 'DC Fast' },
  { id: 'level_2', label: 'Level 2' },
]

export function DiscoveryView({
  chargers,
  merchants,
  userLat,
  userLng,
  isLoading,
  hasError,
  searchQuery,
  onSearchChange,
  selectedFilters,
  onFilterToggle,
  onChargerSelect,
  onMerchantSelect,
  onRefresh,
  likedMerchants,
  onToggleLike,
  activeSession,
  onSearchSubmit,
  onClearSearch,
  searchLocation,
  isSearching,
  vehicle,
  onSearchArea,
  walletBalanceCents,
  onWalletTap,
}: DiscoveryViewProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [sheetPosition, setSheetPosition] = useState<SheetPosition>('half')
  const [selectedConnectors, setSelectedConnectors] = useState<string[]>([])
  const [mapCenter, setMapCenter] = useState<{ lat: number; lng: number } | null>(null)
  const [showSearch, setShowSearch] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [localSearchQuery, setLocalSearchQuery] = useState('')
  const [mapMovedCenter, setMapMovedCenter] = useState<{ lat: number; lng: number } | null>(null)

  const handleConnectorToggle = useCallback((connector: string) => {
    setSelectedConnectors(prev =>
      prev.includes(connector)
        ? prev.filter(c => c !== connector)
        : [...prev, connector]
    )
  }, [])

  const handleSearchSubmit = useCallback(() => {
    if (localSearchQuery.trim()) {
      onSearchChange(localSearchQuery)
      onSearchSubmit?.(localSearchQuery.trim())
      setShowSearch(false)
    }
  }, [localSearchQuery, onSearchChange, onSearchSubmit])

  const handleClearSearch = useCallback(() => {
    setMapCenter(null)
    setLocalSearchQuery('')
    onSearchChange('')
    onClearSearch?.()
  }, [onSearchChange, onClearSearch])

  // Recenter map when geocoded search location changes
  useEffect(() => {
    if (searchLocation) {
      setMapCenter({ lat: searchLocation.lat, lng: searchLocation.lng })
    }
  }, [searchLocation])

  // Active session charger ID for check-in status
  const activeChargerId = activeSession?.chargerId ?? null

  // Filter and combine chargers + merchants into unified list
  const filteredItems: DiscoveryItem[] = useMemo(() => {
    const items: DiscoveryItem[] = []

    const filteredChargers = chargers.filter((c) => {
      if (c.num_evse != null && c.num_evse < 2) return false

      // Connector type filter
      if (selectedConnectors.length > 0) {
        const chargerConnectors = (c.connector_types || []).map(ct => ct.toLowerCase())
        const chargerNetwork = (c.network_name || '').toLowerCase()
        const chargerPower = c.power_kw || 0

        const matchesConnector = selectedConnectors.some(filter => {
          switch (filter) {
            case 'ccs': return chargerConnectors.some(ct => ct.includes('ccs'))
            case 'tesla': return chargerNetwork.includes('tesla') || chargerConnectors.some(ct => ct.includes('tesla'))
            case 'chademo': return chargerConnectors.some(ct => ct.includes('chademo'))
            case 'j1772': return chargerConnectors.some(ct => ct.includes('j1772'))
            case 'dc_fast': return chargerPower > 50
            case 'level_2': return chargerPower > 0 && chargerPower <= 50
            default: return false
          }
        })
        if (!matchesConnector) return false
      }

      if (!searchQuery.trim()) return true
      const q = searchQuery.toLowerCase()
      return (
        c.name.toLowerCase().includes(q) ||
        (c.network_name || '').toLowerCase().includes(q)
      )
    })

    const filteredMerchants = merchants.filter((m) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        const nameMatch = m.name.toLowerCase().includes(q)
        const typeMatch = (m.types || []).some((t) => t.toLowerCase().includes(q))
        if (!nameMatch && !typeMatch) return false
      }

      if (selectedFilters.length > 0) {
        const types = (m.types || []).map((t) => t.toLowerCase())
        return selectedFilters.every((filter) => {
          switch (filter) {
            case 'bathroom': return true
            case 'food': return types.some(t => t.includes('restaurant') || t.includes('food') || t.includes('cafe') || t.includes('bakery'))
            case 'wifi': return types.some(t => t.includes('cafe') || t.includes('restaurant') || t.includes('coffee'))
            case 'pets': return types.some(t => t.includes('pet') || t.includes('veterinary'))
            default: return false
          }
        })
      }
      return true
    })

    for (const charger of filteredChargers) {
      items.push({ type: 'charger', data: charger })
    }
    for (const merchant of filteredMerchants) {
      items.push({ type: 'merchant', data: merchant })
    }

    return items
  }, [chargers, merchants, searchQuery, selectedFilters, selectedConnectors])

  const handlePinTap = useCallback(
    (id: string) => {
      setSelectedId(id)
      // Open charger/merchant detail directly on pin tap
      const item = filteredItems.find((i) => getItemId(i) === id)
      if (item) {
        if (item.type === 'charger') {
          onChargerSelect(item.data)
        } else {
          onMerchantSelect(item.data.place_id, item.data.photo_url)
        }
      } else if (sheetPosition === 'peek') {
        setSheetPosition('half')
      }
    },
    [filteredItems, sheetPosition, onChargerSelect, onMerchantSelect]
  )

  const handleCardSelect = useCallback(
    (id: string) => {
      setSelectedId(id)
      setTimeout(() => {
        const item = filteredItems.find((i) => getItemId(i) === id)
        if (!item) return
        if (item.type === 'charger') {
          onChargerSelect(item.data)
        } else {
          onMerchantSelect(item.data.place_id, item.data.photo_url)
        }
      }, 300)
    },
    [filteredItems, onChargerSelect, onMerchantSelect]
  )

  const handleRecenter = useCallback(() => {
    setSelectedId(null)
    setMapMovedCenter(null)
    if (userLat && userLng) {
      setMapCenter({ lat: userLat, lng: userLng })
    } else {
      setMapCenter(null)
    }
    onClearSearch?.()
  }, [onClearSearch, userLat, userLng])

  const handleMapMoved = useCallback((center: { lat: number; lng: number }) => {
    if (!userLat || !userLng) return
    // Show "Search this area" if user panned >500m from their location
    const dlat = center.lat - userLat
    const dlng = center.lng - userLng
    const distKm = Math.sqrt(dlat * dlat + dlng * dlng) * 111
    if (distKm > 0.5) {
      setMapMovedCenter(center)
    } else {
      setMapMovedCenter(null)
    }
  }, [userLat, userLng])

  const handleSearchThisArea = useCallback(() => {
    if (mapMovedCenter && onSearchArea) {
      onSearchArea(mapMovedCenter.lat, mapMovedCenter.lng)
      setMapMovedCenter(null)
    }
  }, [mapMovedCenter, onSearchArea])

  const activeFilterCount = selectedConnectors.length + selectedFilters.length

  return (
    <div className="flex-1 relative overflow-hidden">
      {/* Map — full bleed */}
      <DiscoveryMap
        items={filteredItems}
        selectedId={selectedId}
        onPinTap={handlePinTap}
        userLat={userLat}
        userLng={userLng}
        onRecenter={handleRecenter}
        sheetPosition={sheetPosition}
        activeChargerId={activeChargerId}
        mapCenter={mapCenter}
        onMapMoved={handleMapMoved}
      />

      {/* Active session banner removed — charging state shown on vehicle card */}

      {/* Chargeway-style Floating Buttons — right side */}
      <div className="absolute right-3 top-3 z-[1500] flex flex-col gap-2.5">
        {/* Search */}
        <button
          onClick={() => {
            setLocalSearchQuery(searchQuery)
            setShowSearch(true)
          }}
          className="w-11 h-11 bg-white shadow-md border border-gray-200 rounded-full flex items-center justify-center active:scale-95 transition-transform"
          aria-label="Search"
        >
          <Search className="w-5 h-5 text-[#050505]" />
        </button>

        {/* Filters */}
        <button
          onClick={() => setShowFilters(true)}
          className="w-11 h-11 bg-white shadow-md border border-gray-200 rounded-full flex items-center justify-center active:scale-95 transition-transform relative"
          aria-label="Filters"
        >
          <SlidersHorizontal className="w-5 h-5 text-[#050505]" />
          {activeFilterCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-[#1877F2] rounded-full text-[10px] font-bold text-white flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </button>

        {/* Recenter */}
        <button
          onClick={handleRecenter}
          className="w-11 h-11 bg-white shadow-md border border-gray-200 rounded-full flex items-center justify-center active:scale-95 transition-transform"
          aria-label="Center on my location"
        >
          <LocateFixed className="w-5 h-5 text-[#1877F2]" />
        </button>
      </div>

      {/* Search Location Banner */}
      {searchLocation && (
        <div className="absolute top-3 left-3 right-16 z-[1500]">
          <div className="bg-white shadow-md border border-gray-200 rounded-2xl px-4 py-2.5 flex items-center justify-between">
            <span className="text-sm text-[#050505] truncate">
              {isSearching ? 'Searching...' : `Near ${searchLocation.name}`}
            </span>
            <button
              onClick={handleClearSearch}
              className="text-sm font-medium text-[#1877F2] whitespace-nowrap ml-2"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {hasError && (
        <div className="absolute top-16 left-3 right-3 z-[2001] bg-red-50 border border-red-200 rounded-2xl px-4 py-2.5 flex items-center justify-between shadow-md">
          <span className="text-sm text-red-700">Couldn't load chargers</span>
          <button onClick={onRefresh} className="text-sm font-medium text-red-600 underline">Retry</button>
        </div>
      )}

      {/* Search This Area — Google Maps style */}
      {mapMovedCenter && onSearchArea && !selectedId && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[1501]">
          <button
            onClick={handleSearchThisArea}
            className="bg-white shadow-lg rounded-full px-5 py-2.5 text-sm font-medium text-[#050505] border border-gray-200 active:scale-95 transition-transform flex items-center gap-2"
          >
            <Search className="w-4 h-4 text-[#1877F2]" />
            Search this area
          </button>
        </div>
      )}

      {/* Bottom Sheet — only when a charger is selected */}
      {selectedId && (
        <DiscoverySheet
          items={filteredItems}
          selectedId={selectedId}
          onSelectItem={handleCardSelect}
          position={sheetPosition}
          onPositionChange={setSheetPosition}
          likedMerchants={likedMerchants}
          onToggleLike={onToggleLike}
          onRefresh={onRefresh}
          isLoading={isLoading}
        />
      )}

      {/* Vehicle Card — Chargeway-style bottom card */}
      {!selectedId && !searchLocation && vehicle && (
        <div className="absolute bottom-3 left-3 right-3 z-[1500]">
          {vehicle.connected ? (
            <div className="bg-[#1A1A2E] rounded-2xl shadow-lg overflow-hidden">
              <button
                onClick={vehicle.onTap}
                className="w-full px-4 pt-3 pb-2 flex items-center gap-2 active:scale-[0.99] transition-transform"
              >
                {/* Left: text info */}
                <div className="flex-1 text-left min-w-0">
                  <p className="font-bold text-white text-base leading-tight">
                    {vehicle.name || getCleanModelName(vehicle.vehicleModel)}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {[vehicle.vehicleYear, getCleanModelName(vehicle.vehicleModel), vehicle.exteriorColor].filter(Boolean).join(' · ')}
                  </p>
                  {/* Battery bar */}
                  {vehicle.batteryPercent != null && (
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className={`text-sm font-bold ${
                        vehicle.batteryPercent > 50 ? 'text-green-400' :
                        vehicle.batteryPercent > 20 ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {vehicle.batteryPercent}%
                      </span>
                      <div className="flex-1 h-2.5 bg-white/10 rounded-full overflow-hidden max-w-[120px]">
                        <div
                          className={`h-full rounded-full transition-all ${
                            vehicle.batteryPercent > 50 ? 'bg-green-400' :
                            vehicle.batteryPercent > 20 ? 'bg-yellow-400' : 'bg-red-400'
                          }`}
                          style={{ width: `${Math.min(100, vehicle.batteryPercent)}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
                {/* Right: Tesla logo */}
                <div className="w-16 h-16 flex-shrink-0 flex items-center justify-center">
                  <img src="/tesla-t-logo.png" alt="Tesla" className="w-12 h-12 object-contain" />
                </div>
              </button>
              {/* Charging status row */}
              {vehicle.isCharging && (
                <div className="px-4 py-2.5 border-t border-white/10 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2 flex-shrink-0">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-400" />
                    </span>
                    <span className="text-xs font-semibold text-green-400">Charging Active</span>
                  </div>
                  <span className="text-xs font-medium text-gray-300">
                    {vehicle.minutesToFull != null && vehicle.minutesToFull > 0
                      ? `${vehicle.minutesToFull} min remaining`
                      : (vehicle.durationMinutes ?? 0) > 0
                        ? `${vehicle.durationMinutes} min`
                        : 'Just started'}
                    {vehicle.kwhDelivered != null ? ` · ${vehicle.kwhDelivered.toFixed(1)} kWh` : ''}
                  </span>
                </div>
              )}
              {/* Wallet balance row */}
              {walletBalanceCents != null && (
                <button
                  onClick={onWalletTap}
                  className="w-full px-4 py-2 border-t border-white/10 flex items-center justify-between active:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 bg-green-500/20 rounded-full flex items-center justify-center">
                      <span className="text-[10px] font-bold text-green-400">$</span>
                    </div>
                    <span className="text-xs text-gray-400">Wallet</span>
                  </div>
                  <span className="text-sm font-semibold text-white">
                    ${(walletBalanceCents / 100).toFixed(2)}
                  </span>
                </button>
              )}
            </div>
          ) : (
            <button
              onClick={vehicle.onConnect}
              className="w-full bg-white rounded-2xl shadow-lg px-4 py-3.5 flex items-center gap-3 active:scale-[0.98] transition-transform border border-gray-100"
            >
              <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
                <Zap className="w-5 h-5 text-gray-400" />
              </div>
              <p className="flex-1 text-left font-medium text-[#050505] text-sm">Add your vehicle</p>
              <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-lg text-gray-500">+</span>
              </div>
            </button>
          )}
        </div>
      )}

      {/* Search Overlay */}
      {showSearch && (
        <div className="fixed inset-0 z-[2500] bg-white flex flex-col">
          <div className="flex items-center gap-3 px-4 pt-[env(safe-area-inset-top)] pb-4">
            <button
              onClick={() => setShowSearch(false)}
              className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0"
            >
              <X className="w-5 h-5 text-[#050505]" />
            </button>
            <h2 className="text-lg font-semibold text-[#050505]">Search</h2>
          </div>
          <div className="px-4">
            <input
              type="text"
              autoFocus
              placeholder="Search chargers, places, or addresses"
              value={localSearchQuery}
              onChange={e => setLocalSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearchSubmit()}
              className="w-full bg-gray-100 text-[#050505] placeholder:text-gray-400 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-[#1877F2] text-base"
            />
          </div>
        </div>
      )}

      {/* Filters Overlay */}
      {showFilters && (
        <div className="fixed inset-0 z-[2500] bg-white flex flex-col">
          <div className="flex items-center justify-between px-4 pt-[env(safe-area-inset-top)] pb-4">
            <button
              onClick={() => setShowFilters(false)}
              className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center"
            >
              <X className="w-5 h-5 text-[#050505]" />
            </button>
            <h2 className="text-lg font-semibold text-[#050505]">Filters</h2>
            <button
              onClick={() => {
                setSelectedConnectors([])
                selectedFilters.forEach(f => onFilterToggle(f))
              }}
              className="text-sm text-[#65676B]"
            >
              Reset
            </button>
          </div>

          <div className="flex-1 px-4 overflow-y-auto">
            {/* Connector Types */}
            <h3 className="text-sm font-semibold text-[#050505] mb-3 mt-2">Plug Type</h3>
            <div className="grid grid-cols-2 gap-2 mb-6">
              {connectorTypes.map(ct => {
                const isSelected = selectedConnectors.includes(ct.id)
                return (
                  <button
                    key={ct.id}
                    onClick={() => handleConnectorToggle(ct.id)}
                    className={`px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                      isSelected
                        ? 'bg-[#1877F2] text-white'
                        : 'bg-gray-100 text-[#050505]'
                    }`}
                  >
                    {ct.label}
                  </button>
                )
              })}
            </div>

            {/* Amenity Filters */}
            <h3 className="text-sm font-semibold text-[#050505] mb-3">Amenities</h3>
            <div className="grid grid-cols-2 gap-2 mb-6">
              {(['bathroom', 'food', 'wifi', 'pets'] as const).map(filter => {
                const isSelected = selectedFilters.includes(filter)
                const labels: Record<string, string> = { bathroom: 'Bathroom', food: 'Food', wifi: 'WiFi', pets: 'Pet Friendly' }
                return (
                  <button
                    key={filter}
                    onClick={() => onFilterToggle(filter)}
                    className={`px-4 py-3 rounded-xl text-sm font-medium transition-colors ${
                      isSelected
                        ? 'bg-[#1877F2] text-white'
                        : 'bg-gray-100 text-[#050505]'
                    }`}
                  >
                    {labels[filter]}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="px-4 pb-[env(safe-area-inset-bottom)] pb-4">
            <button
              onClick={() => setShowFilters(false)}
              className="w-full py-3 bg-[#1877F2] text-white font-semibold rounded-xl"
            >
              Show Results
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
