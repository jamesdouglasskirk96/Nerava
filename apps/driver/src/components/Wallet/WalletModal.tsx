import { X, TrendingUp, TrendingDown, Clock } from 'lucide-react'

interface Transaction {
  id: string
  type: 'credit' | 'withdrawal'
  description: string
  amount: number
  timestamp: string
}

interface ActiveSession {
  id: string
  merchantName: string
  remainingMinutes: number
}

interface WalletModalProps {
  isOpen: boolean
  onClose: () => void
  balance: number
  pendingBalance: number
  activeSessions: ActiveSession[]
  recentTransactions: Transaction[]
  onWithdraw: () => void
}

export function WalletModal({
  isOpen,
  onClose,
  balance,
  pendingBalance,
  activeSessions,
  recentTransactions,
  onWithdraw,
}: WalletModalProps) {
  if (!isOpen) return null

  const formatCurrency = (cents: number) => {
    return `$${(cents / 100).toFixed(2)}`
  }

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
              <path d="M21 18v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v1"/>
              <path d="M16 12h5v2h-5a1 1 0 0 1 0-2z"/>
            </svg>
            <span className="text-lg font-semibold">My Wallet</span>
          </div>
          <button
            onClick={onClose}
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

            <button
              onClick={onWithdraw}
              disabled={balance < 1000}
              className="w-full mt-4 py-3 bg-white text-[#1877F2] font-semibold rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Withdraw to Bank
            </button>
            <p className="text-center text-sm opacity-80 mt-2">Minimum $10 • Instant</p>
          </div>

          {/* How it works */}
          <div className="bg-gray-50 rounded-xl p-4">
            <p className="font-semibold mb-3">How it works:</p>
            <ul className="space-y-2 text-sm text-[#65676B]">
              <li className="flex items-start gap-2">
                <span className="text-[#1877F2]">•</span>
                Earn credits from exclusives
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#1877F2]">•</span>
                Cashback from card-linked offers
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#1877F2]">•</span>
                Withdraw anytime to your bank
              </li>
            </ul>
          </div>

          {/* Active Sessions */}
          {activeSessions.length > 0 && (
            <div>
              <h3 className="font-semibold mb-3">Active Sessions</h3>
              <div className="space-y-2">
                {activeSessions.map((session) => (
                  <div
                    key={session.id}
                    className="bg-gray-50 rounded-xl p-4 flex items-center justify-between"
                  >
                    <div>
                      <p className="font-medium">{session.merchantName}</p>
                      <p className="text-sm text-[#65676B]">{session.remainingMinutes} min remaining</p>
                    </div>
                    <div className="px-3 py-1.5 bg-gradient-to-r from-yellow-500/15 to-amber-500/15 rounded-full border border-yellow-600/30">
                      <span className="text-xs font-medium text-yellow-700">⭐ Exclusive</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Activity */}
          {recentTransactions.length > 0 && (
            <div>
              <h3 className="font-semibold mb-3">Recent Activity</h3>
              <div className="space-y-3">
                {recentTransactions.map((tx) => (
                  <div key={tx.id} className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      tx.type === 'credit' ? 'bg-green-100' : 'bg-red-100'
                    }`}>
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
                    <span className={`font-semibold ${
                      tx.type === 'credit' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {tx.type === 'credit' ? '+' : '-'}{formatCurrency(tx.amount)}
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
