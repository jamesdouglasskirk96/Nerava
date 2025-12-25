import { useState, useEffect } from 'react'
import './Users.css'

interface User {
  id: number
  public_id: string
  email: string
  role_flags: string
  is_active: boolean
  created_at: string
}

interface UserWallet {
  user_id: number
  balance_cents: number
  nova_balance: number
  transactions: Array<{
    id: number
    cents: number
    reason: string
    meta: Record<string, any>
    created_at: string
  }>
}

export default function Users() {
  const [users, setUsers] = useState<User[]>([])
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [wallet, setWallet] = useState<UserWallet | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [adjustAmount, setAdjustAmount] = useState('')
  const [adjustReason, setAdjustReason] = useState('')
  const [showAdjustModal, setShowAdjustModal] = useState(false)

  useEffect(() => {
    if (searchQuery) {
      searchUsers()
    }
  }, [searchQuery])

  const searchUsers = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/v1/admin/users?query=${encodeURIComponent(searchQuery)}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token') || ''}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setUsers(data)
      } else {
        console.error('Failed to search users:', response.statusText)
      }
    } catch (error) {
      console.error('Error searching users:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadUserWallet = async (userId: number) => {
    setLoading(true)
    try {
      const response = await fetch(`/v1/admin/users/${userId}/wallet`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('admin_token') || ''}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setWallet(data)
      } else {
        console.error('Failed to load wallet:', response.statusText)
      }
    } catch (error) {
      console.error('Error loading wallet:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUserClick = (user: User) => {
    setSelectedUser(user)
    loadUserWallet(user.id)
  }

  const handleAdjustWallet = async () => {
    if (!selectedUser || !adjustAmount || !adjustReason) return

    setLoading(true)
    try {
      const response = await fetch(`/v1/admin/users/${selectedUser.id}/wallet/adjust`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('admin_token') || ''}`
        },
        body: JSON.stringify({
          amount_cents: parseInt(adjustAmount),
          reason: adjustReason
        })
      })
      if (response.ok) {
        await loadUserWallet(selectedUser.id)
        setShowAdjustModal(false)
        setAdjustAmount('')
        setAdjustReason('')
        alert('Wallet adjusted successfully')
      } else {
        const error = await response.json()
        alert(`Failed to adjust wallet: ${error.detail || response.statusText}`)
      }
    } catch (error) {
      console.error('Error adjusting wallet:', error)
      alert('Error adjusting wallet')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="users-page">
      <h1>Users</h1>
      
      <div className="search-section">
        <input
          type="text"
          placeholder="Search by email, name, or public_id..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="content-grid">
        <div className="users-list">
          <h2>Search Results</h2>
          {loading && <p>Loading...</p>}
          {!loading && users.length === 0 && searchQuery && <p>No users found</p>}
          {!loading && users.length === 0 && !searchQuery && <p>Enter a search query to find users</p>}
          {users.map(user => (
            <div
              key={user.id}
              className={`user-card ${selectedUser?.id === user.id ? 'selected' : ''}`}
              onClick={() => handleUserClick(user)}
            >
              <div className="user-email">{user.email}</div>
              <div className="user-meta">
                <span>ID: {user.public_id}</span>
                <span>Roles: {user.role_flags || 'none'}</span>
              </div>
            </div>
          ))}
        </div>

        {selectedUser && wallet && (
          <div className="user-detail">
            <h2>User Details</h2>
            <div className="detail-section">
              <h3>{selectedUser.email}</h3>
              <p>ID: {selectedUser.public_id}</p>
              <p>Roles: {selectedUser.role_flags || 'none'}</p>
            </div>

            <div className="detail-section">
              <h3>Wallet</h3>
              <p>Balance: ${(wallet.balance_cents / 100).toFixed(2)}</p>
              <p>Nova Balance: {wallet.nova_balance}</p>
              <button
                className="btn-primary"
                onClick={() => setShowAdjustModal(true)}
              >
                Adjust Wallet
              </button>
            </div>

            <div className="detail-section">
              <h3>Recent Transactions</h3>
              <div className="transactions-list">
                {wallet.transactions.slice(0, 20).map(tx => (
                  <div key={tx.id} className="transaction-item">
                    <div className="tx-amount">${(tx.cents / 100).toFixed(2)}</div>
                    <div className="tx-reason">{tx.reason}</div>
                    <div className="tx-date">{new Date(tx.created_at).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {showAdjustModal && selectedUser && (
        <div className="modal-overlay" onClick={() => setShowAdjustModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Adjust Wallet</h2>
            <p>User: {selectedUser.email}</p>
            <div className="form-group">
              <label>Amount (cents, positive for credit, negative for debit)</label>
              <input
                type="number"
                value={adjustAmount}
                onChange={(e) => setAdjustAmount(e.target.value)}
                placeholder="e.g., 1000 or -500"
              />
            </div>
            <div className="form-group">
              <label>Reason</label>
              <input
                type="text"
                value={adjustReason}
                onChange={(e) => setAdjustReason(e.target.value)}
                placeholder="Reason for adjustment"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowAdjustModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleAdjustWallet} disabled={loading}>
                {loading ? 'Processing...' : 'Adjust'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

