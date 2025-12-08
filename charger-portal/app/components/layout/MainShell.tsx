'use client'

import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import type { Property, DateRangeKey } from '@/lib/types/dashboard'

interface MainShellProps {
  children: React.ReactNode
  selectedProperty: Property
  properties: Property[]
  onPropertyChange: (propertyId: string) => void
  dateRange: DateRangeKey
  onDateRangeChange: (range: DateRangeKey) => void
  activeNavItem?: string
}

export function MainShell({
  children,
  selectedProperty,
  properties,
  onPropertyChange,
  dateRange,
  onDateRangeChange,
  activeNavItem = 'overview',
}: MainShellProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar activeNavItem={activeNavItem} />
      
      {/* Main content area */}
      <div className="lg:pl-64">
        <TopBar
          selectedProperty={selectedProperty}
          properties={properties}
          onPropertyChange={onPropertyChange}
          dateRange={dateRange}
          onDateRangeChange={onDateRangeChange}
        />
        
        {/* Page content */}
        <main className="p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  )
}

