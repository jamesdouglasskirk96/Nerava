'use client'

import { useSavingsDashboard } from './useSavingsDashboard'
import type { AutoTopUpConfig } from '../types/dashboard'

export function useNovaBudget() {
  const dashboard = useSavingsDashboard()

  return {
    budget: dashboard.novaBudget,
    autoTopUpConfig: dashboard.autoTopUpConfig,
    purchaseNova: dashboard.purchaseNova,
    updateAutoTopUp: dashboard.updateAutoTopUp,
    isLoading: dashboard.isLoading,
  }
}

