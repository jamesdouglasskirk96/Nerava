'use client'

import { MainShell } from './MainShell'
import { useSavingsDashboard } from '@/lib/hooks/useSavingsDashboard'

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const dashboard = useSavingsDashboard()

  return (
    <MainShell
      selectedProperty={dashboard.selectedProperty}
      properties={dashboard.properties}
      onPropertyChange={dashboard.setSelectedProperty}
      dateRange={dashboard.dateRange}
      onDateRangeChange={dashboard.setDateRange}
      activeNavItem="overview"
    >
      {children}
    </MainShell>
  )
}

