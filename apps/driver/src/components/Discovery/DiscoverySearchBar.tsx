import { Search, X } from 'lucide-react'
import type { AmenityFilter } from './discovery-types'

interface DiscoverySearchBarProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  selectedFilters: string[]
  onFilterToggle: (filter: string) => void
  selectedConnectors?: string[]
  onConnectorToggle?: (connector: string) => void
  onSearchSubmit?: (query: string) => void
  onClearSearch?: () => void
}

const amenityIcons: Record<AmenityFilter, string> = {
  Bathroom: '\ud83d\udebb',
  Food: '\ud83c\udf74',
  WiFi: '\ud83d\udcf6',
  Pets: '\ud83d\udc15',
  Music: '\ud83c\udfb5',
}

const filters: AmenityFilter[] = ['Bathroom', 'Food', 'WiFi', 'Pets', 'Music']

const connectorTypes = [
  { id: 'ccs', label: 'CCS', icon: '\u26a1' },
  { id: 'tesla', label: 'Tesla', icon: '\ud83d\udd34' },
  { id: 'chademo', label: 'CHAdeMO', icon: '\u26a1' },
  { id: 'j1772', label: 'J1772', icon: '\ud83d\udd0c' },
]

export function DiscoverySearchBar({
  searchQuery,
  onSearchChange,
  selectedFilters,
  onFilterToggle,
  selectedConnectors = [],
  onConnectorToggle,
  onSearchSubmit,
  onClearSearch,
}: DiscoverySearchBarProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchQuery.trim() && onSearchSubmit) {
      onSearchSubmit(searchQuery.trim())
    }
  }

  const handleClear = () => {
    onSearchChange('')
    onClearSearch?.()
  }

  return (
    <div className="px-3 pt-2 pb-2">
      {/* Search Input */}
      <div className="h-12 bg-white/95 backdrop-blur-md border border-[#E4E6EB] rounded-full px-4 flex items-center gap-3 shadow-[0_2px_12px_rgba(0,0,0,0.1)]">
        <Search className="w-5 h-5 text-[#656A6B] flex-shrink-0" />
        <input
          type="text"
          placeholder="Search chargers, places, or addresses"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-transparent outline-none text-[#050505] placeholder:text-[#656A6B] text-base"
        />
        {searchQuery.trim() && (
          <button
            onClick={handleClear}
            className="p-1 rounded-full hover:bg-[#F7F8FA] transition-colors flex-shrink-0"
          >
            <X className="w-4 h-4 text-[#656A6B]" />
          </button>
        )}
      </div>

      {/* Connector Filter Pills */}
      {onConnectorToggle && (
        <div className="flex gap-2 overflow-x-auto no-scrollbar mt-2 px-1">
          {connectorTypes.map((ct) => {
            const isSelected = selectedConnectors.includes(ct.id)
            return (
              <button
                key={ct.id}
                onClick={() => onConnectorToggle(ct.id)}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-full whitespace-nowrap transition-all shadow-sm text-xs font-medium ${
                  isSelected
                    ? 'bg-[#1877F2] text-white shadow-md'
                    : 'bg-white/90 backdrop-blur-md border border-[#E4E6EB] text-[#656A6B]'
                }`}
              >
                <span>{ct.icon}</span>
                <span>{ct.label}</span>
              </button>
            )
          })}
          {/* DC Fast / Level 2 toggles */}
          <button
            onClick={() => onConnectorToggle('dc_fast')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-full whitespace-nowrap transition-all shadow-sm text-xs font-medium ${
              selectedConnectors.includes('dc_fast')
                ? 'bg-[#1877F2] text-white shadow-md'
                : 'bg-white/90 backdrop-blur-md border border-[#E4E6EB] text-[#656A6B]'
            }`}
          >
            <span>\u26a1</span>
            <span>DC Fast</span>
          </button>
          <button
            onClick={() => onConnectorToggle('level_2')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-full whitespace-nowrap transition-all shadow-sm text-xs font-medium ${
              selectedConnectors.includes('level_2')
                ? 'bg-[#10B981] text-white shadow-md'
                : 'bg-white/90 backdrop-blur-md border border-[#E4E6EB] text-[#656A6B]'
            }`}
          >
            <span>\ud83d\udd0c</span>
            <span>Level 2</span>
          </button>
        </div>
      )}

      {/* Amenity Filter Pills */}
      <div className="flex gap-2 overflow-x-auto no-scrollbar mt-2 px-1">
        {filters.map((filter) => {
          const isSelected = selectedFilters.includes(filter.toLowerCase())
          return (
            <button
              key={filter}
              onClick={() => onFilterToggle(filter.toLowerCase())}
              className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-full whitespace-nowrap transition-all shadow-sm ${
                isSelected
                  ? 'bg-[#1877F2] text-white shadow-md'
                  : 'bg-white/90 backdrop-blur-md border border-[#E4E6EB] text-[#656A6B]'
              }`}
            >
              <span className="text-sm">{amenityIcons[filter]}</span>
              <span className={`text-[10px] font-medium ${isSelected ? 'text-white' : 'text-[#656A6B]'}`}>{filter}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
