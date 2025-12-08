'use client'

import { useState } from 'react'
import { DashboardLayout } from './components/layout/DashboardLayout'
import { useSavingsDashboard } from '@/lib/hooks/useSavingsDashboard'
import { KpiCards } from './components/dashboard/KpiCards'
import { SavingsOverTimeChart } from './components/charts/SavingsOverTimeChart'
import { OffPeakVsPeakChart } from './components/charts/OffPeakVsPeakChart'
import { NovaBudgetPanel } from './components/dashboard/NovaBudgetPanel'
import { ActivityFeed } from './components/dashboard/ActivityFeed'
import { SessionsTable } from './components/dashboard/SessionsTable'
import { BuyNovaDialog } from './components/dashboard/BuyNovaDialog'

export default function DashboardPage() {
  const dashboard = useSavingsDashboard()
  const [isBuyNovaDialogOpen, setIsBuyNovaDialogOpen] = useState(false)
  const [buyNovaTab, setBuyNovaTab] = useState<'one-time' | 'auto-topup'>('one-time')

  const handleBuyNovaClick = () => {
    setBuyNovaTab('one-time')
    setIsBuyNovaDialogOpen(true)
  }

  const handleManageAutoTopUpClick = () => {
    setBuyNovaTab('auto-topup')
    setIsBuyNovaDialogOpen(true)
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">Savings Dashboard</h1>
        <p className="text-gray-600">
          Overview of your EV charging savings and driver rewards
        </p>
      </div>

      {/* KPI Cards */}
      <KpiCards kpis={dashboard.kpis} isLoading={dashboard.isLoading} />

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Savings Over Time</h3>
          <SavingsOverTimeChart data={dashboard.dailySavings} />
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Session Distribution</h3>
          <OffPeakVsPeakChart data={dashboard.sessionSplit} />
        </div>
      </div>

      {/* Nova Budget & Activity Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <NovaBudgetPanel
          budget={dashboard.novaBudget}
          autoTopUpConfig={dashboard.autoTopUpConfig}
          onBuyNovaClick={handleBuyNovaClick}
          onManageAutoTopUpClick={handleManageAutoTopUpClick}
          isLoading={dashboard.isLoading}
        />
        <ActivityFeed activity={dashboard.activity} isLoading={dashboard.isLoading} />
      </div>

      {/* Sessions Table */}
      <SessionsTable sessions={dashboard.sessions} isLoading={dashboard.isLoading} />

      {/* Buy Nova Dialog */}
      <BuyNovaDialog
        isOpen={isBuyNovaDialogOpen}
        onClose={() => setIsBuyNovaDialogOpen(false)}
        onOneTimePurchase={dashboard.purchaseNova}
        onAutoTopUpSave={dashboard.updateAutoTopUp}
        currentAutoTopUpConfig={dashboard.autoTopUpConfig}
        initialTab={buyNovaTab}
      />
      </div>
    </DashboardLayout>
  )
}

