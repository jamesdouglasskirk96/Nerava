import { useState, useCallback } from 'react'
import { Building2, Plus, Trash2, Loader2, CheckCircle, CreditCard } from 'lucide-react'
import { usePlaidLinkToken, useFundingSources, api } from '../../services/api'
import { useQueryClient } from '@tanstack/react-query'

interface FundingSource {
  id: string
  institution_name: string | null
  account_mask: string | null
  account_type: string | null
  is_default: boolean
}

interface BankLinkFlowProps {
  onLinkComplete?: () => void
}

export function BankLinkFlow({ onLinkComplete }: BankLinkFlowProps) {
  const queryClient = useQueryClient()
  const { data: linkTokenData, refetch: refetchLinkToken } = usePlaidLinkToken()
  const { data: fundingData, isLoading: loadingSources } = useFundingSources()
  const [linking, setLinking] = useState(false)
  const [removing, setRemoving] = useState<string | null>(null)
  const [error, setError] = useState('')

  const sources = fundingData?.funding_sources || []
  const hasLinkedAccount = sources.length > 0

  const handleOpenPlaidLink = useCallback(async () => {
    setError('')
    setLinking(true)

    try {
      // Use the Plaid Link drop-in script (not the React hook)
      if (!linkTokenData?.link_token) {
        await refetchLinkToken()
      }

      const token = linkTokenData?.link_token
      if (!token) {
        setError('Failed to initialize bank linking')
        setLinking(false)
        return
      }

      // Open Plaid Link via the global handler
      const Plaid = (window as any).Plaid
      if (Plaid) {
        const handler = Plaid.create({
          token,
          onSuccess: async (publicToken: string, metadata: any) => {
            try {
              const accountId = metadata.accounts?.[0]?.id || metadata.account_id
              await api.post('/v1/wallet/plaid/exchange', {
                public_token: publicToken,
                account_id: accountId,
              })
              queryClient.invalidateQueries({ queryKey: ['funding-sources'] })
              queryClient.invalidateQueries({ queryKey: ['wallet'] })
              onLinkComplete?.()
            } catch {
              setError('Failed to link bank account')
            }
            setLinking(false)
          },
          onExit: () => {
            setLinking(false)
          },
        })
        handler.open()
      } else {
        // Fallback: load Plaid Link script
        const script = document.createElement('script')
        script.src = 'https://cdn.plaid.com/link/v2/stable/link-initialize.js'
        script.onload = () => {
          const PlaidLoaded = (window as any).Plaid
          if (PlaidLoaded) {
            const handler = PlaidLoaded.create({
              token,
              onSuccess: async (publicToken: string, metadata: any) => {
                try {
                  const accountId = metadata.accounts?.[0]?.id || metadata.account_id
                  await api.post('/v1/wallet/plaid/exchange', {
                    public_token: publicToken,
                    account_id: accountId,
                  })
                  queryClient.invalidateQueries({ queryKey: ['funding-sources'] })
                  queryClient.invalidateQueries({ queryKey: ['wallet'] })
                  onLinkComplete?.()
                } catch {
                  setError('Failed to link bank account')
                }
                setLinking(false)
              },
              onExit: () => {
                setLinking(false)
              },
            })
            handler.open()
          }
        }
        document.head.appendChild(script)
      }
    } catch {
      setError('Failed to open bank linking')
      setLinking(false)
    }
  }, [linkTokenData, refetchLinkToken, queryClient, onLinkComplete])

  const handleRemoveSource = async (sourceId: string) => {
    setRemoving(sourceId)
    try {
      await api.delete(`/v1/wallet/funding-sources/${sourceId}`)
      queryClient.invalidateQueries({ queryKey: ['funding-sources'] })
    } catch {
      setError('Failed to remove account')
    }
    setRemoving(null)
  }

  return (
    <div className="space-y-4">
      {/* Linked Accounts */}
      {loadingSources ? (
        <div className="flex items-center justify-center py-6">
          <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
        </div>
      ) : hasLinkedAccount ? (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">Linked Accounts</p>
          {sources.map((source: FundingSource) => (
            <div key={source.id} className="flex items-center gap-3 bg-gray-50 rounded-xl p-3 border border-gray-200">
              <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center">
                {source.account_type === 'debit_card' ? (
                  <CreditCard className="w-5 h-5 text-blue-600" />
                ) : (
                  <Building2 className="w-5 h-5 text-blue-600" />
                )}
              </div>
              <div className="flex-1">
                <p className="font-medium text-sm">{source.institution_name || 'Bank Account'}</p>
                <p className="text-xs text-gray-500">
                  {source.account_type === 'debit_card' ? 'Debit Card' : 'Checking'} ····{source.account_mask || '****'}
                </p>
              </div>
              {source.is_default && (
                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Default</span>
              )}
              <button
                onClick={() => handleRemoveSource(source.id)}
                disabled={removing === source.id}
                className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
              >
                {removing === source.id ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-4">
          <Building2 className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-sm text-gray-600 mb-1">No bank account linked</p>
          <p className="text-xs text-gray-400">Link your bank to withdraw rewards via ACH</p>
        </div>
      )}

      {/* Link / Add Account Button */}
      <button
        onClick={handleOpenPlaidLink}
        disabled={linking}
        className="w-full py-3 bg-[#1877F2] text-white font-semibold rounded-xl hover:bg-[#166FE5] disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
      >
        {linking ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> Connecting...</>
        ) : hasLinkedAccount ? (
          <><Plus className="w-4 h-4" /> Add Another Account</>
        ) : (
          <><Building2 className="w-4 h-4" /> Link Bank Account</>
        )}
      </button>

      {/* Success indicator */}
      {hasLinkedAccount && (
        <div className="flex items-center gap-2 text-sm text-green-600">
          <CheckCircle className="w-4 h-4" />
          <span>Ready for ACH withdrawals (1-2 business days)</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <p className="text-sm text-red-600 text-center">{error}</p>
      )}
    </div>
  )
}
