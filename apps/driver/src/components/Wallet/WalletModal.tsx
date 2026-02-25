import { useState } from 'react'
import { X, TrendingUp, TrendingDown, Clock, Loader2, ExternalLink, CheckCircle, AlertCircle } from 'lucide-react'
import {
  createStripeAccount,
  createStripeAccountLink,
  requestWithdrawal,
} from '../../services/api'

export interface Transaction {
  id: string
  type: 'credit' | 'withdrawal'
  description: string
  amount: number
  timestamp: string
}

interface WalletModalProps {
  isOpen: boolean
  onClose: () => void
  balance: number
  pendingBalance: number
  stripeOnboardingComplete: boolean
  recentTransactions: Transaction[]
  onBalanceChanged: () => void
  userEmail?: string
}

const MINIMUM_WITHDRAWAL_CENTS = 2000 // $20 — must match backend

type WithdrawStep = 'idle' | 'amount' | 'confirming' | 'processing' | 'success' | 'error'

export function WalletModal({
  isOpen,
  onClose,
  balance,
  pendingBalance,
  stripeOnboardingComplete,
  recentTransactions,
  onBalanceChanged,
  userEmail,
}: WalletModalProps) {
  const [withdrawStep, setWithdrawStep] = useState<WithdrawStep>('idle')
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [connectingBank, setConnectingBank] = useState(false)

  if (!isOpen) return null

  const formatCurrency = (cents: number) => `$${(cents / 100).toFixed(2)}`

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)
    if (diffHours < 1) return 'Just now'
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  const canWithdraw = balance >= MINIMUM_WITHDRAWAL_CENTS

  const handleConnectBank = async () => {
    setConnectingBank(true)
    setErrorMessage('')
    try {
      const appUrl = window.location.origin
      // Create Express account first
      await createStripeAccount(userEmail || '')
      // Then get the onboarding link
      const { url } = await createStripeAccountLink(
        `${appUrl}/?stripe_return=true`,
        `${appUrl}/?stripe_refresh=true`,
      )
      window.location.href = url
    } catch (e: any) {
      setErrorMessage(e?.message || 'Failed to start bank setup')
      setConnectingBank(false)
    }
  }

  const handleStartWithdraw = () => {
    setWithdrawAmount((balance / 100).toFixed(2))
    setWithdrawStep('amount')
    setErrorMessage('')
  }

  const parsedAmountCents = Math.round(parseFloat(withdrawAmount || '0') * 100)
  const amountValid = parsedAmountCents >= MINIMUM_WITHDRAWAL_CENTS && parsedAmountCents <= balance

  const handleConfirmWithdraw = async () => {
    if (!amountValid) return
    setWithdrawStep('processing')
    setErrorMessage('')
    try {
      await requestWithdrawal(parsedAmountCents)
      setWithdrawStep('success')
      onBalanceChanged()
    } catch (e: any) {
      const msg = e?.message || 'Withdrawal failed'
      // If backend says account not set up, redirect to onboarding
      if (msg.includes('not set up') || msg.includes('not complete')) {
        setWithdrawStep('idle')
        handleConnectBank()
        return
      }
      setErrorMessage(msg)
      setWithdrawStep('error')
    }
  }

  const resetWithdraw = () => {
    setWithdrawStep('idle')
    setWithdrawAmount('')
    setErrorMessage('')
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-end justify-center sm:items-center">
      <div
        className="bg-white w-full max-w-md rounded-t-3xl sm:rounded-3xl max-h-[90vh] overflow-hidden flex flex-col"
        style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#E4E6EB]">
          <div className="flex items-center gap-2">
            <svg className="w-6 h-6 text-[#1877F2]" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21 18v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v1" />
              <path d="M16 12h5v2h-5a1 1 0 0 1 0-2z" />
            </svg>
            <span className="text-lg font-semibold">My Wallet</span>
          </div>
          <button
            onClick={() => { resetWithdraw(); onClose() }}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Balance Card */}
          <div className="bg-[#1877F2] rounded-2xl p-5 text-white">
            <p className="text-sm opacity-90">Your Balance</p>
            <p className="text-4xl font-bold mt-1">{formatCurrency(balance)}</p>
            {pendingBalance > 0 && (
              <p className="text-sm opacity-80 mt-1">+ {formatCurrency(pendingBalance)} pending</p>
            )}

            {/* Withdraw / Connect Bank Flow */}
            {withdrawStep === 'idle' && (
              <>
                {stripeOnboardingComplete ? (
                  <button
                    onClick={handleStartWithdraw}
                    disabled={!canWithdraw}
                    className="w-full mt-4 py-3 bg-white text-[#1877F2] font-semibold rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Withdraw to Bank
                  </button>
                ) : (
                  <button
                    onClick={handleConnectBank}
                    disabled={connectingBank}
                    className="w-full mt-4 py-3 bg-white text-[#1877F2] font-semibold rounded-xl hover:bg-gray-50 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                  >
                    {connectingBank ? (
                      <><Loader2 className="w-4 h-4 animate-spin" /> Setting up...</>
                    ) : (
                      <><ExternalLink className="w-4 h-4" /> Connect Your Bank</>
                    )}
                  </button>
                )}
                <p className="text-center text-sm opacity-80 mt-2">
                  {stripeOnboardingComplete ? `Minimum ${formatCurrency(MINIMUM_WITHDRAWAL_CENTS)}` : 'Required for withdrawals'}
                </p>
              </>
            )}

            {/* Amount Input */}
            {withdrawStep === 'amount' && (
              <div className="mt-4 space-y-3">
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#1877F2] font-semibold text-lg">$</span>
                  <input
                    type="number"
                    step="0.01"
                    min={MINIMUM_WITHDRAWAL_CENTS / 100}
                    max={balance / 100}
                    value={withdrawAmount}
                    onChange={(e) => setWithdrawAmount(e.target.value)}
                    className="w-full py-3 pl-8 pr-4 bg-white text-[#1877F2] font-semibold rounded-xl text-lg focus:outline-none focus:ring-2 focus:ring-white/50"
                    autoFocus
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={resetWithdraw}
                    className="flex-1 py-2.5 bg-white/20 text-white font-medium rounded-xl hover:bg-white/30 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleConfirmWithdraw}
                    disabled={!amountValid}
                    className="flex-1 py-2.5 bg-white text-[#1877F2] font-semibold rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Confirm
                  </button>
                </div>
                {!amountValid && withdrawAmount && (
                  <p className="text-center text-sm opacity-80">
                    {parsedAmountCents < MINIMUM_WITHDRAWAL_CENTS
                      ? `Minimum ${formatCurrency(MINIMUM_WITHDRAWAL_CENTS)}`
                      : `Maximum ${formatCurrency(balance)}`}
                  </p>
                )}
              </div>
            )}

            {/* Processing */}
            {withdrawStep === 'processing' && (
              <div className="mt-4 flex flex-col items-center gap-2 py-3">
                <Loader2 className="w-6 h-6 animate-spin" />
                <p className="text-sm opacity-90">Processing withdrawal...</p>
              </div>
            )}

            {/* Success */}
            {withdrawStep === 'success' && (
              <div className="mt-4 space-y-3">
                <div className="flex flex-col items-center gap-2 py-2">
                  <CheckCircle className="w-8 h-8" />
                  <p className="font-semibold">Withdrawal submitted</p>
                  <p className="text-sm opacity-80">{formatCurrency(parsedAmountCents)} is on its way to your bank</p>
                </div>
                <button
                  onClick={resetWithdraw}
                  className="w-full py-2.5 bg-white text-[#1877F2] font-semibold rounded-xl hover:bg-gray-50 transition-colors"
                >
                  Done
                </button>
              </div>
            )}

            {/* Error */}
            {withdrawStep === 'error' && (
              <div className="mt-4 space-y-3">
                <div className="flex flex-col items-center gap-2 py-2">
                  <AlertCircle className="w-8 h-8" />
                  <p className="font-semibold">Withdrawal failed</p>
                  <p className="text-sm opacity-80 text-center">{errorMessage}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={resetWithdraw}
                    className="flex-1 py-2.5 bg-white/20 text-white font-medium rounded-xl hover:bg-white/30 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleConfirmWithdraw}
                    className="flex-1 py-2.5 bg-white text-[#1877F2] font-semibold rounded-xl hover:bg-gray-50 transition-colors"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Error banner (for connect bank failures) */}
          {errorMessage && withdrawStep === 'idle' && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">
              {errorMessage}
            </div>
          )}

          {/* How it works */}
          <div className="bg-gray-50 rounded-xl p-4">
            <p className="font-semibold mb-3">How it works:</p>
            <ul className="space-y-2 text-sm text-[#65676B]">
              <li className="flex items-start gap-2">
                <span className="text-[#1877F2]">•</span>
                Earn rewards from charging sessions
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#1877F2]">•</span>
                Sponsored incentives at eligible locations
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#1877F2]">•</span>
                Withdraw anytime to your bank
              </li>
            </ul>
          </div>

          {/* Recent Activity */}
          {recentTransactions.length === 0 && (
            <p className="text-sm text-[#65676B] text-center py-4">
              Your charging rewards will appear here
            </p>
          )}
          {recentTransactions.length > 0 && (
            <div>
              <h3 className="font-semibold mb-3">Recent Activity</h3>
              <div className="space-y-3">
                {recentTransactions.map((tx) => (
                  <div key={tx.id} className="flex items-center gap-3">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        tx.type === 'credit' ? 'bg-green-100' : 'bg-red-100'
                      }`}
                    >
                      {tx.type === 'credit' ? (
                        <TrendingUp className="w-5 h-5 text-green-600" />
                      ) : (
                        <TrendingDown className="w-5 h-5 text-red-600" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{tx.description}</p>
                      <p className="text-xs text-[#65676B] flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTimeAgo(tx.timestamp)}
                      </p>
                    </div>
                    <span
                      className={`font-semibold ${
                        tx.type === 'credit' ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {tx.type === 'credit' ? '+' : '-'}
                      {formatCurrency(tx.amount)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
