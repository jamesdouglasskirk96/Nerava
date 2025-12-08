'use client'

import { useState, useEffect } from 'react'
import { Modal } from '../ui/Modal'
import { Tabs } from '../ui/Tabs'
import { PrimaryButton } from '../ui/Button'
import type { AutoTopUpConfig } from '@/lib/types/dashboard'
import { NOVA_PER_USD } from '@/lib/types/dashboard'

const NOVA_PER_USD_VALUE = NOVA_PER_USD

interface BuyNovaDialogProps {
  isOpen: boolean
  onClose: () => void
  onOneTimePurchase: (amountUsd: number, note?: string) => Promise<void>
  onAutoTopUpSave: (config: AutoTopUpConfig) => Promise<void>
  currentAutoTopUpConfig?: AutoTopUpConfig
  initialTab?: 'one-time' | 'auto-topup'
}

export function BuyNovaDialog({
  isOpen,
  onClose,
  onOneTimePurchase,
  onAutoTopUpSave,
  currentAutoTopUpConfig,
  initialTab = 'one-time',
}: BuyNovaDialogProps) {
  const [activeTab, setActiveTab] = useState(initialTab)
  
  // Reset form and set tab when dialog opens
  useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab)
      setAmountUsd('')
      setNote('')
    }
  }, [isOpen, initialTab])
  const [isSubmitting, setIsSubmitting] = useState(false)

  // One-time purchase state
  const [amountUsd, setAmountUsd] = useState('')
  const [note, setNote] = useState('')

  // Auto top-up state
  const [autoTopUpEnabled, setAutoTopUpEnabled] = useState(
    currentAutoTopUpConfig?.enabled || false
  )
  const [threshold, setThreshold] = useState(
    currentAutoTopUpConfig?.threshold.toString() || '3000'
  )
  const [topUpAmountUsd, setTopUpAmountUsd] = useState(
    currentAutoTopUpConfig?.topUpAmountUsd.toString() || '500'
  )
  const [frequency, setFrequency] = useState(
    currentAutoTopUpConfig?.frequency || 'No limit'
  )

  const novaAmount = amountUsd ? parseFloat(amountUsd) * NOVA_PER_USD_VALUE : 0
  const topUpNovaAmount = topUpAmountUsd ? parseFloat(topUpAmountUsd) * NOVA_PER_USD_VALUE : 0

  const handleOneTimePurchase = async () => {
    if (!amountUsd || parseFloat(amountUsd) <= 0) return

    setIsSubmitting(true)
    try {
      await onOneTimePurchase(parseFloat(amountUsd), note || undefined)
      // Reset form
      setAmountUsd('')
      setNote('')
      onClose()
    } catch (error) {
      console.error('Purchase failed:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleAutoTopUpSave = async () => {
    if (!threshold || !topUpAmountUsd) return

    setIsSubmitting(true)
    try {
      const config: AutoTopUpConfig = {
        enabled: autoTopUpEnabled,
        threshold: parseInt(threshold),
        topUpAmountUsd: parseFloat(topUpAmountUsd),
        topUpAmountNova: topUpNovaAmount,
        frequency,
      }
      await onAutoTopUpSave(config)
      onClose()
    } catch (error) {
      console.error('Auto top-up save failed:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const tabs = [
    { id: 'one-time', label: 'One-time purchase' },
    { id: 'auto-topup', label: 'Auto top-up' },
  ]

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Buy Nova" className="max-w-2xl">
      <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} className="mb-6" />

      {activeTab === 'one-time' && (
        <div className="space-y-6">
          <div>
            <label htmlFor="amount-usd" className="block text-sm font-semibold text-gray-700 mb-2">
              Amount (USD)
            </label>
            <input
              id="amount-usd"
              type="number"
              min="1"
              step="0.01"
              value={amountUsd}
              onChange={(e) => setAmountUsd(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              placeholder="Enter amount in USD"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Nova Amount (calculated)
            </label>
            <div className="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg text-gray-900">
              {novaAmount > 0 ? novaAmount.toLocaleString() : '0'} Nova
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Rate: 1 USD = {NOVA_PER_USD_VALUE} Nova
            </p>
          </div>

          <div>
            <label htmlFor="note" className="block text-sm font-semibold text-gray-700 mb-2">
              Optional Note
            </label>
            <input
              id="note"
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              placeholder="e.g., January off-peak promo"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <PrimaryButton
              onClick={handleOneTimePurchase}
              disabled={!amountUsd || parseFloat(amountUsd) <= 0 || isSubmitting}
            >
              {isSubmitting ? 'Processing...' : 'Confirm purchase'}
            </PrimaryButton>
          </div>
        </div>
      )}

      {activeTab === 'auto-topup' && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="enable-auto-topup"
              checked={autoTopUpEnabled}
              onChange={(e) => setAutoTopUpEnabled(e.target.checked)}
              className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
            />
            <label htmlFor="enable-auto-topup" className="text-sm font-semibold text-gray-700">
              Enable auto top-up
            </label>
          </div>

          {autoTopUpEnabled && (
            <>
              <div>
                <label htmlFor="threshold" className="block text-sm font-semibold text-gray-700 mb-2">
                  When remaining Nova is below:
                </label>
                <input
                  id="threshold"
                  type="number"
                  min="1"
                  value={threshold}
                  onChange={(e) => setThreshold(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="3000"
                />
                <p className="text-xs text-gray-500 mt-1">Trigger top-up when balance falls below this amount</p>
              </div>

              <div>
                <label htmlFor="topup-amount" className="block text-sm font-semibold text-gray-700 mb-2">
                  Top-up amount (USD)
                </label>
                <input
                  id="topup-amount"
                  type="number"
                  min="1"
                  step="0.01"
                  value={topUpAmountUsd}
                  onChange={(e) => setTopUpAmountUsd(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {topUpNovaAmount > 0 ? `${topUpNovaAmount.toLocaleString()} Nova` : '0 Nova'} will be purchased
                </p>
              </div>

              <div>
                <label htmlFor="frequency" className="block text-sm font-semibold text-gray-700 mb-2">
                  Frequency Limit (optional)
                </label>
                <select
                  id="frequency"
                  value={frequency}
                  onChange={(e) => setFrequency(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  <option>No limit</option>
                  <option>Max 1 per month</option>
                  <option>Max 2 per month</option>
                  <option>Max 4 per month</option>
                </select>
              </div>
            </>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <PrimaryButton
              onClick={handleAutoTopUpSave}
              disabled={isSubmitting || (autoTopUpEnabled && (!threshold || !topUpAmountUsd))}
            >
              {isSubmitting ? 'Saving...' : 'Save auto top-up settings'}
            </PrimaryButton>
          </div>
        </div>
      )}
    </Modal>
  )
}

