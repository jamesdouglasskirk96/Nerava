'use client'

import type { Property, DateRangeKey } from '@/lib/types/dashboard'

interface TopBarProps {
  selectedProperty: Property
  properties: Property[]
  onPropertyChange: (propertyId: string) => void
  dateRange: DateRangeKey
  onDateRangeChange: (range: DateRangeKey) => void
}

const dateRangeOptions: { key: DateRangeKey; label: string }[] = [
  { key: 'LAST_30_DAYS', label: 'Last 30 days' },
  { key: 'THIS_MONTH', label: 'This month' },
  { key: 'LAST_90_DAYS', label: 'Last 90 days' },
]

export function TopBar({
  selectedProperty,
  properties,
  onPropertyChange,
  dateRange,
  onDateRangeChange,
}: TopBarProps) {
  return (
    <div className="bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        {/* Left: Property selector */}
        <div className="flex items-center gap-4">
          <label htmlFor="property-select" className="text-sm font-semibold text-gray-700">
            Property:
          </label>
          <select
            id="property-select"
            value={selectedProperty.id}
            onChange={(e) => onPropertyChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-900 bg-white hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            {properties.map((property) => (
              <option key={property.id} value={property.id}>
                {property.name}
              </option>
            ))}
          </select>
        </div>

        {/* Center: Date range selector */}
        <div className="flex items-center gap-2">
          {dateRangeOptions.map((option) => (
            <button
              key={option.key}
              onClick={() => onDateRangeChange(option.key)}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-colors
                ${
                  dateRange === option.key
                    ? 'bg-primary text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
              `}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* Right: User menu placeholder */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary-soft rounded-full flex items-center justify-center">
            <span className="text-primary text-sm font-semibold">
              {selectedProperty.name.charAt(0)}
            </span>
          </div>
          <span className="text-sm font-medium text-gray-700 hidden sm:inline">
            Account
          </span>
        </div>
      </div>
    </div>
  )
}

