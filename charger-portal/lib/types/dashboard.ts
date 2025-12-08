export type DateRangeKey = 'LAST_30_DAYS' | 'THIS_MONTH' | 'LAST_90_DAYS'

export interface Property {
  id: string
  name: string
}

export interface DateRange {
  key: DateRangeKey
  label: string
}

export interface Kpi {
  monthlySavings: number // USD
  novaPurchased: number // Nova amount
  rewardsIssued: number // USD (gift card value)
  activeDrivers: number // Count
}

export interface DailySavings {
  date: string // ISO date string
  savingsUsd: number
}

export interface SessionSplit {
  type: 'off-peak' | 'peak'
  count: number
}

export interface Session {
  id: string
  driverName: string
  dateTime: string // ISO datetime
  sessionType: 'off-peak' | 'peak'
  energyKwh: number
  estimatedCost: number // USD
  novaAwarded: number
}

export type ActivityType = 'SAVINGS' | 'REWARD' | 'TOP_UP' | 'PURCHASE' | 'SYSTEM'

export interface ActivityItem {
  id: string
  timestamp: string // ISO datetime
  type: ActivityType
  description: string
}

export interface NovaBudget {
  total: number // Total Nova in budget
  spent: number // Nova spent this period
  remaining: number // Calculated: total - spent
  totalUsd: number // Total budget in USD (for display)
  projectedRunoutDate: string | null // ISO date or null if no projection
}

export interface AutoTopUpConfig {
  enabled: boolean
  threshold: number // When remaining Nova is below this, trigger top-up
  topUpAmountUsd: number
  topUpAmountNova: number // Calculated from USD
  frequency?: string // Optional frequency limit
}

export interface DashboardData {
  property: Property
  kpis: Kpi
  dailySavings: DailySavings[]
  sessionSplit: SessionSplit[]
  sessions: Session[]
  activity: ActivityItem[]
  novaBudget: NovaBudget
  autoTopUpConfig: AutoTopUpConfig
}

// Conversion rate constant
export const NOVA_PER_USD = 10

