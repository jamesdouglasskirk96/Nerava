'use client'

import { Card } from '../ui/Card'
import { PrimaryButton } from '../ui/Button'
import type { NovaBudget, AutoTopUpConfig } from '@/lib/types/dashboard'

interface NovaBudgetPanelProps {
  budget: NovaBudget
  autoTopUpConfig: AutoTopUpConfig
  onBuyNovaClick: () => void
  onManageAutoTopUpClick: () => void
  isLoading?: boolean
}

export function NovaBudgetPanel({
  budget,
  autoTopUpConfig,
  onBuyNovaClick,
  onManageAutoTopUpClick,
  isLoading = false,
}: NovaBudgetPanelProps) {
  const percentUsed = budget.total > 0 ? (budget.spent / budget.total) * 100 : 0

  if (isLoading) {
    return (
      <Card className="animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded w-full"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <div className="space-y-6">
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Nova Budget</h3>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-semibold text-gray-700">Current budget:</span>
              <span className="text-sm font-medium text-gray-900">
                {budget.total.toLocaleString()} Nova (${budget.totalUsd.toLocaleString()})
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm font-semibold text-gray-700">Spent this period:</span>
              <span className="text-sm font-medium text-gray-900">
                {budget.spent.toLocaleString()} Nova
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm font-semibold text-gray-700">Remaining:</span>
              <span className="text-sm font-medium text-primary">
                {budget.remaining.toLocaleString()} Nova
              </span>
            </div>
            
            {budget.projectedRunoutDate && (
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-gray-700">Projected runout:</span>
                <span className="text-sm font-medium text-gray-900">
                  {new Date(budget.projectedRunoutDate).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-medium text-gray-700">Budget used</span>
            <span className="text-xs font-medium text-gray-700">{percentUsed.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-primary h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${Math.min(percentUsed, 100)}%` }}
            />
          </div>
        </div>

        {/* Auto top-up status */}
        {autoTopUpConfig.enabled && (
          <div className="p-3 bg-primary-soft rounded-lg">
            <p className="text-xs font-medium text-primary">
              Auto top-up ON: ${autoTopUpConfig.topUpAmountUsd.toLocaleString()} when balance &lt;{' '}
              {autoTopUpConfig.threshold.toLocaleString()} Nova
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="space-y-3 pt-2">
          <PrimaryButton onClick={onBuyNovaClick} className="w-full">
            Buy Nova
          </PrimaryButton>
          <button
            onClick={onManageAutoTopUpClick}
            className="w-full text-sm text-primary hover:text-primary-dark font-medium transition-colors"
          >
            Manage auto top-up
          </button>
        </div>
      </div>
    </Card>
  )
}

