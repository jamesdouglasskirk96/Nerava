import { useState, useEffect } from 'react';
import { Eye, Ban, CheckCircle, Search, Mail, ExternalLink, Pause, Play, ChevronLeft, ChevronRight } from 'lucide-react';
import { searchMerchants, listMerchants, sendMerchantPortalLink, pauseMerchant, resumeMerchant, banMerchant, verifyMerchant, type Merchant } from '../services/api';

export function Merchants() {
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [sendingEmail, setSendingEmail] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pauseDialog, setPauseDialog] = useState<{ merchantId: string; action: 'pause' | 'resume' | 'ban' | 'verify' } | null>(null);
  const [reason, setReason] = useState('');
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [emailDialog, setEmailDialog] = useState<{ merchantId: string; email: string } | null>(null);
  const [total, setTotal] = useState(0);
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [isSearchMode, setIsSearchMode] = useState(false);

  useEffect(() => {
    if (!isSearchMode) {
      loadMerchants();
    }
  }, [offset, isSearchMode]);

  const loadMerchants = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listMerchants(limit, offset);
      setMerchants(data.merchants);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load merchants:', err);
      setError('Failed to load merchants. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      setIsSearchMode(false);
      setOffset(0);
      return;
    }
    try {
      setLoading(true);
      setIsSearchMode(true);
      const data = await searchMerchants(searchTerm);
      setMerchants(data.merchants);
      setTotal(data.merchants.length);
      setOffset(0);
    } catch (err) {
      console.error('Failed to search merchants:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSendPortalLink = async (merchantId: string) => {
    setEmailDialog({ merchantId, email: '' });
  };

  const confirmSendPortalLink = async () => {
    if (!emailDialog || !emailDialog.email) {
      setFeedback({ type: 'error', message: 'Please enter an email address' });
      setTimeout(() => setFeedback(null), 5000);
      return;
    }

    try {
      setSendingEmail(emailDialog.merchantId);
      await sendMerchantPortalLink(emailDialog.merchantId, emailDialog.email);
      setFeedback({ type: 'success', message: 'Portal link sent successfully!' });
      setTimeout(() => setFeedback(null), 5000);
      setEmailDialog(null);
    } catch (err: any) {
      console.error('Failed to send portal link:', err);
      setFeedback({ type: 'error', message: err.message || 'Failed to send portal link' });
      setTimeout(() => setFeedback(null), 5000);
    } finally {
      setSendingEmail(null);
    }
  };

  const handleViewPortal = (merchantId: string) => {
    const portalUrl = import.meta.env.VITE_MERCHANT_PORTAL_URL || 'https://merchant.nerava.network';
    window.open(`${portalUrl}?merchant_id=${merchantId}&admin_preview=true`, '_blank');
  };

  const handlePauseResume = (merchantId: string, action: 'pause' | 'resume' | 'ban' | 'verify') => {
    setPauseDialog({ merchantId, action });
  };

  const confirmPauseResume = async () => {
    if (!pauseDialog || !reason || reason.length < 5) {
      setFeedback({ type: 'error', message: 'Please provide a reason (minimum 5 characters)' });
      setTimeout(() => setFeedback(null), 5000);
      return;
    }

    try {
      if (pauseDialog.action === 'pause') {
        await pauseMerchant(pauseDialog.merchantId, reason);
      } else if (pauseDialog.action === 'resume') {
        await resumeMerchant(pauseDialog.merchantId, reason);
      } else if (pauseDialog.action === 'ban') {
        await banMerchant(pauseDialog.merchantId, reason);
      } else if (pauseDialog.action === 'verify') {
        await verifyMerchant(pauseDialog.merchantId, reason);
      }
      const pastTense = pauseDialog.action === 'verify' ? 'verified' : `${pauseDialog.action}ned`;
      setFeedback({ type: 'success', message: `Merchant ${pastTense} successfully` });
      setTimeout(() => setFeedback(null), 5000);
      setPauseDialog(null);
      setReason('');
      loadMerchants(); // Refresh
    } catch (err: any) {
      console.error(`Failed to ${pauseDialog.action} merchant:`, err);
      setFeedback({ type: 'error', message: err.message || `Failed to ${pauseDialog.action} merchant` });
      setTimeout(() => setFeedback(null), 5000);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-700 bg-green-50 border-green-200';
      case 'paused': return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'flagged': return 'text-red-700 bg-red-50 border-red-200';
      default: return 'text-neutral-700 bg-neutral-50 border-neutral-200';
    }
  };

  if (loading) {
    return <div className="p-8"><p>Loading merchants...</p></div>;
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
          <button onClick={loadMerchants} className="ml-4 underline">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl text-neutral-900">Merchants</h1>
        <p className="text-sm text-neutral-600 mt-1">Manage and monitor merchant accounts</p>
      </div>

      {feedback && (
        <div
          className={`mb-4 border rounded-lg p-4 ${
            feedback.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-700'
              : 'bg-red-50 border-red-200 text-red-700'
          }`}
        >
          {feedback.message}
        </div>
      )}

      {/* Search */}
      <div className="mb-6 flex gap-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-400" />
          <input
            type="text"
            placeholder="Search merchants..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full pl-10 pr-4 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-neutral-900 text-white rounded-lg hover:bg-neutral-800"
        >
          Search
        </button>
      </div>

      {/* Merchants Table */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-neutral-50 border-b border-neutral-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">ID</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Zone</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs text-neutral-600 uppercase tracking-wider">Nova Balance</th>
              <th className="px-6 py-3 text-right text-xs text-neutral-600 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {merchants.map((merchant) => (
              <tr key={merchant.id} className="hover:bg-neutral-50">
                <td className="px-6 py-4 text-sm text-neutral-900 font-mono">{merchant.id.slice(0, 8)}...</td>
                <td className="px-6 py-4 text-sm text-neutral-900">{merchant.name}</td>
                <td className="px-6 py-4 text-sm text-neutral-600">{merchant.zone_slug || '-'}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex px-2.5 py-1 rounded-md text-xs border ${getStatusColor(merchant.status)}`}>
                    {merchant.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-neutral-900">{merchant.nova_balance}</td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleViewPortal(merchant.id)}
                      className="p-1.5 hover:bg-neutral-100 rounded text-neutral-600 hover:text-neutral-900"
                      title="View Portal"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleSendPortalLink(merchant.id)}
                      disabled={sendingEmail === merchant.id}
                      className="p-1.5 hover:bg-blue-50 rounded text-blue-600 hover:text-blue-700 disabled:opacity-50"
                      title="Send Portal Link"
                    >
                      <Mail className="w-4 h-4" />
                    </button>
                    {merchant.status === 'paused' ? (
                      <button
                        onClick={() => handlePauseResume(merchant.id, 'resume')}
                        className="p-1.5 hover:bg-green-50 rounded text-green-600 hover:text-green-700"
                        title="Resume Merchant"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handlePauseResume(merchant.id, 'pause')}
                        className="p-1.5 hover:bg-yellow-50 rounded text-yellow-600 hover:text-yellow-700"
                        title="Pause Merchant"
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                    )}
                    {merchant.status !== 'verified' && (
                      <button
                        onClick={() => handlePauseResume(merchant.id, 'verify')}
                        className="p-1.5 hover:bg-green-50 rounded text-green-600 hover:text-green-700"
                        title="Verify Merchant"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    )}
                    {merchant.status !== 'banned' && (
                      <button
                        onClick={() => handlePauseResume(merchant.id, 'ban')}
                        className="p-1.5 hover:bg-red-50 rounded text-red-600 hover:text-red-700"
                        title="Ban Merchant"
                      >
                        <Ban className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {merchants.length === 0 && (
        <div className="text-center py-12 text-neutral-500">No merchants found</div>
      )}

      {/* Pagination Controls */}
      {!isSearchMode && total > limit && (
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-neutral-600">
            Showing {offset + 1} to {Math.min(offset + limit, total)} of {total} merchants
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total}
              className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Pause/Resume Dialog */}
      {pauseDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">
              {pauseDialog.action === 'pause' ? 'Pause' : 'Resume'} Merchant
            </h3>
            <p className="text-sm text-neutral-600 mb-4">
              Please provide a reason for this action (minimum 5 characters):
            </p>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg mb-4"
              rows={3}
              placeholder="Enter reason..."
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setPauseDialog(null);
                  setReason('');
                }}
                className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmPauseResume}
                disabled={!reason || reason.length < 5}
                className={`px-4 py-2 rounded-lg text-white ${
                  pauseDialog.action === 'pause'
                    ? 'bg-yellow-600 hover:bg-yellow-700'
                    : 'bg-green-600 hover:bg-green-700'
                } disabled:bg-neutral-300`}
              >
                Confirm {pauseDialog.action === 'pause' ? 'Pause' : 'Resume'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Email Dialog */}
      {emailDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Send Portal Link</h3>
            <p className="text-sm text-neutral-600 mb-4">
              Enter merchant email address:
            </p>
            <input
              type="email"
              value={emailDialog.email}
              onChange={(e) => setEmailDialog({ ...emailDialog, email: e.target.value })}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg mb-4"
              placeholder="merchant@example.com"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setEmailDialog(null)}
                className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50"
                disabled={sendingEmail === emailDialog.merchantId}
              >
                Cancel
              </button>
              <button
                onClick={confirmSendPortalLink}
                disabled={!emailDialog.email || sendingEmail === emailDialog.merchantId}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-neutral-300"
              >
                {sendingEmail === emailDialog.merchantId ? 'Sending...' : 'Send'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
