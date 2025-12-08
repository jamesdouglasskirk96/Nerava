import { Card } from '../ui/Card'
import type { Kpi } from '@/lib/types/dashboard'

interface KpiCardsProps {
  kpis: Kpi
  isLoading?: boolean
}

export function KpiCards({ kpis, isLoading = false }: KpiCardsProps) {
  const kpiData = [
    {
      label: 'Estimated Monthly Savings',
      value: `$${kpis.monthlySavings.toLocaleString()}`,
      subtext: 'vs. baseline without off-peak incentives',
    },
    {
      label: 'Nova Purchased',
      value: `${kpis.novaPurchased.toLocaleString()} Nova`,
      subtext: 'This period',
    },
    {
      label: 'Rewards Issued to Drivers',
      value: `$${kpis.rewardsIssued.toLocaleString()}`,
      subtext: 'Gift card value',
    },
    {
      label: 'Active EV Drivers',
      value: kpis.activeDrivers.toString(),
      subtext: 'Charged at least once this month',
    },
  ]

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-12 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-full"></div>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-8">
      {kpiData.map((kpi, index) => (
        <Card key={index}>
          <div className="space-y-2">
            <p className="text-sm font-semibold text-gray-700">{kpi.label}</p>
            <p className="text-3xl sm:text-4xl font-bold text-gray-900">{kpi.value}</p>
            <p className="text-xs text-gray-500">{kpi.subtext}</p>
          </div>
        </Card>
      ))}
    </div>
  )
}

