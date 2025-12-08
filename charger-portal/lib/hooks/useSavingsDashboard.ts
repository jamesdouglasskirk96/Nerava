'use client'

import { useState, useMemo } from 'react'
import { mockDashboardData, mockProperties } from '../mock/mockDashboardData'
import type {
  DashboardData,
  Property,
  DateRangeKey,
  AutoTopUpConfig,
  ActivityItem,
} from '../types/dashboard'
import { NOVA_PER_USD } from '../types/dashboard'

const NOVA_PER_USD_VALUE = NOVA_PER_USD

export interface UseSavingsDashboardReturn {
  // Data
  selectedProperty: Property
  properties: Property[]
  dateRange: DateRangeKey
  kpis: DashboardData['kpis']
  dailySavings: DashboardData['dailySavings']
  sessionSplit: DashboardData['sessionSplit']
  sessions: DashboardData['sessions']
  activity: DashboardData['activity']
  novaBudget: DashboardData['novaBudget']
  autoTopUpConfig: DashboardData['autoTopUpConfig']
  
  // State setters
  setSelectedProperty: (propertyId: string) => void
  setDateRange: (range: DateRangeKey) => void
  
  // Actions
  purchaseNova: (amountUsd: number, note?: string) => Promise<void>
  updateAutoTopUp: (config: AutoTopUpConfig) => Promise<void>
  
  // Loading state
  isLoading: boolean
}

export function useSavingsDashboard(): UseSavingsDashboardReturn {
  const [selectedPropertyId, setSelectedPropertyId] = useState<string>(
    mockProperties[0].id
  )
  const [dateRange, setDateRange] = useState<DateRangeKey>('LAST_30_DAYS')
  const [isLoading, setIsLoading] = useState(false)
  
  // In-memory state for dynamic updates
  const [dynamicState, setDynamicState] = useState<Record<string, Partial<DashboardData>>>({})

  // Get base data for selected property
  const baseData = mockDashboardData[selectedPropertyId]
  
  // Merge with dynamic state updates
  const currentData = useMemo(() => {
    const dynamic = dynamicState[selectedPropertyId] || {}
    return {
      ...baseData,
      ...dynamic,
      novaBudget: {
        ...baseData.novaBudget,
        ...(dynamic.novaBudget || {}),
      },
      autoTopUpConfig: {
        ...baseData.autoTopUpConfig,
        ...(dynamic.autoTopUpConfig || {}),
      },
      activity: dynamic.activity || baseData.activity,
    }
  }, [baseData, dynamicState, selectedPropertyId])

  const setSelectedProperty = (propertyId: string) => {
    setIsLoading(true)
    // Simulate loading delay
    setTimeout(() => {
      setSelectedPropertyId(propertyId)
      setIsLoading(false)
    }, 500)
  }

  const setDateRangeWithLoading = (range: DateRangeKey) => {
    setIsLoading(true)
    setTimeout(() => {
      setDateRange(range)
      setIsLoading(false)
    }, 400)
  }

  const purchaseNova = async (amountUsd: number, note?: string): Promise<void> => {
    setIsLoading(true)
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800))
    
    const novaAmount = amountUsd * NOVA_PER_USD_VALUE
    const currentBudget = currentData.novaBudget
    
    // Update budget
    const newTotal = currentBudget.total + novaAmount
    const newRemaining = currentBudget.remaining + novaAmount
    const newTotalUsd = newTotal / NOVA_PER_USD_VALUE
    
    // Create activity entry
    const newActivity: ActivityItem = {
      id: `activity-${Date.now()}`,
      timestamp: new Date().toISOString(),
      type: 'PURCHASE',
      description: `Purchased ${novaAmount.toLocaleString()} Nova ($${amountUsd.toLocaleString()})${note ? ` - ${note}` : ''}.`,
    }

    // Update state
    setDynamicState(prev => ({
      ...prev,
      [selectedPropertyId]: {
        ...prev[selectedPropertyId],
        novaBudget: {
          ...currentBudget,
          total: newTotal,
          remaining: newRemaining,
          totalUsd: newTotalUsd,
        },
        activity: [newActivity, ...(prev[selectedPropertyId]?.activity || currentData.activity)].slice(0, 8),
      },
    }))
    
    setIsLoading(false)
  }

  const updateAutoTopUp = async (config: AutoTopUpConfig): Promise<void> => {
    setIsLoading(true)
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 600))
    
    // Create activity entry
    const newActivity: ActivityItem = {
      id: `activity-${Date.now()}`,
      timestamp: new Date().toISOString(),
      type: 'SYSTEM',
      description: config.enabled
        ? `Updated auto top-up: $${config.topUpAmountUsd} when balance < ${config.threshold} Nova.`
        : 'Disabled auto top-up.',
    }

    // Update state
    setDynamicState(prev => ({
      ...prev,
      [selectedPropertyId]: {
        ...prev[selectedPropertyId],
        autoTopUpConfig: config,
        activity: [newActivity, ...(prev[selectedPropertyId]?.activity || currentData.activity)].slice(0, 8),
      },
    }))
    
    setIsLoading(false)
  }

  return {
    selectedProperty: currentData.property,
    properties: mockProperties,
    dateRange,
    kpis: currentData.kpis,
    dailySavings: currentData.dailySavings,
    sessionSplit: currentData.sessionSplit,
    sessions: currentData.sessions,
    activity: currentData.activity,
    novaBudget: currentData.novaBudget,
    autoTopUpConfig: currentData.autoTopUpConfig,
    setSelectedProperty,
    setDateRange: setDateRangeWithLoading,
    purchaseNova,
    updateAutoTopUp,
    isLoading,
  }
}

