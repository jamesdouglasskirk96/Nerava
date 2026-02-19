import { useState } from 'react';
import { AlertTriangle, XCircle, StopCircle } from 'lucide-react';
import { forceCloseSessions, emergencyPause } from '../services/api';

export function Overrides() {
  const [selectedLocation, setSelectedLocation] = useState('');
  const [reason, setReason] = useState('');
  const [confirmDialog, setConfirmDialog] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmationToken, setConfirmationToken] = useState('');
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  async function handleForceClose() {
    if (!selectedLocation || !reason || reason.length < 10) {
      setFeedback({ type: 'error', message: 'Location and reason (min 10 chars) required' });
      setTimeout(() => setFeedback(null), 5000);
      return;
    }

    setLoading(true);
    setError(null);
    setFeedback(null);
    try {
      const response = await forceCloseSessions(selectedLocation, reason);
      setFeedback({ type: 'success', message: `Successfully closed ${response.sessions_closed} sessions` });
      setTimeout(() => setFeedback(null), 5000);
      setConfirmDialog(null);
      setReason('');
      setSelectedLocation('');
    } catch (err: any) {
      console.error('Force close failed:', err);
      setError(err.message || 'Failed to force close sessions');
      setFeedback({ type: 'error', message: err.message || 'Failed to force close sessions' });
      setTimeout(() => setFeedback(null), 5000);
    } finally {
      setLoading(false);
    }
  }

  async function handleEmergencyPause(action: 'activate' | 'deactivate') {
    if (!reason || reason.length < 10) {
      setFeedback({ type: 'error', message: 'Reason required (min 10 chars)' });
      setTimeout(() => setFeedback(null), 5000);
      return;
    }

    if (action === 'activate' && confirmationToken !== 'CONFIRM-EMERGENCY-PAUSE') {
      setFeedback({ type: 'error', message: 'Please enter the confirmation token: CONFIRM-EMERGENCY-PAUSE' });
      setTimeout(() => setFeedback(null), 5000);
      return;
    }

    setLoading(true);
    setError(null);
    setFeedback(null);
    try {
      await emergencyPause(action, reason, confirmationToken || 'CONFIRM-EMERGENCY-PAUSE');
      setFeedback({ type: 'success', message: `Emergency pause ${action}d successfully` });
      setTimeout(() => setFeedback(null), 5000);
      setConfirmDialog(null);
      setReason('');
      setConfirmationToken('');
    } catch (err: any) {
      console.error('Emergency pause failed:', err);
      setError(err.message || 'Failed to execute emergency pause');
      setFeedback({ type: 'error', message: err.message || 'Failed to execute emergency pause' });
      setTimeout(() => setFeedback(null), 5000);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-red-600" />
          <div>
            <h1 className="text-2xl text-neutral-900">Overrides</h1>
            <p className="text-sm text-neutral-600 mt-1">
              Critical manual controls - Use with extreme caution
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

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

      {/* Warning Banner */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="text-sm text-red-900">Critical Control Section</h3>
            <p className="text-sm text-red-700 mt-1">
              Actions performed here have immediate system-wide effects and cannot be undone. All
              actions are logged and require operator authentication.
            </p>
          </div>
        </div>
      </div>

      {/* Override Actions */}
      <div className="grid grid-cols-1 gap-4 mb-8">
        {/* Force Close Sessions */}
        <div className="border border-red-300 bg-red-50 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-white border border-red-300">
              <XCircle className="w-6 h-6 text-red-700" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-lg text-neutral-900">Force-Close All Sessions at Location</h3>
                <span className="px-2 py-0.5 rounded text-xs uppercase tracking-wider bg-red-200 text-red-800">
                  critical
                </span>
              </div>
              <p className="text-sm text-neutral-700 mb-4">
                Immediately terminate all active exclusive sessions at a specific merchant location
              </p>
              <div className="space-y-3">
                <input
                  type="text"
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                  placeholder="Enter merchant/location ID"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm bg-white"
                />
                <button
                  onClick={() => setConfirmDialog('force-close')}
                  disabled={!selectedLocation || loading}
                  className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:bg-neutral-300 disabled:cursor-not-allowed"
                >
                  Execute Force-Close
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Emergency Pause */}
        <div className="border border-red-300 bg-red-50 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-white border border-red-300">
              <StopCircle className="w-6 h-6 text-red-700" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-lg text-neutral-900">Emergency Pause</h3>
                <span className="px-2 py-0.5 rounded text-xs uppercase tracking-wider bg-red-200 text-red-800">
                  critical
                </span>
              </div>
              <p className="text-sm text-neutral-700 mb-4">
                Pause all exclusive activations system-wide immediately
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setConfirmDialog('emergency-activate')}
                  disabled={loading}
                  className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:bg-neutral-300"
                >
                  Activate Emergency Pause
                </button>
                <button
                  onClick={() => setConfirmDialog('emergency-deactivate')}
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:bg-neutral-300"
                >
                  Deactivate Emergency Pause
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Dialogs */}
      {confirmDialog === 'force-close' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Force-Close Sessions</h3>
            <p className="text-sm text-neutral-600 mb-4">
              This will immediately close all active sessions at location: <strong>{selectedLocation}</strong>
            </p>
            <p className="text-sm text-neutral-600 mb-4">
              Please provide a reason (minimum 10 characters):
            </p>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg mb-4"
              rows={4}
              placeholder="Enter reason for force-closing sessions..."
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setConfirmDialog(null);
                  setReason('');
                }}
                className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={handleForceClose}
                disabled={loading || !reason || reason.length < 10}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-neutral-300"
              >
                {loading ? 'Executing...' : 'Confirm Force-Close'}
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmDialog === 'emergency-activate' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4 text-red-600">Activate Emergency Pause</h3>
            <p className="text-sm text-neutral-600 mb-4">
              This will pause ALL exclusive activations system-wide. This is a critical action.
            </p>
            <p className="text-sm text-neutral-600 mb-2">
              Please provide a reason (minimum 10 characters):
            </p>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg mb-4"
              rows={3}
              placeholder="Enter reason..."
            />
            <p className="text-sm text-neutral-600 mb-2">
              Confirmation token (type: CONFIRM-EMERGENCY-PAUSE):
            </p>
            <input
              type="text"
              value={confirmationToken}
              onChange={(e) => setConfirmationToken(e.target.value)}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg mb-4"
              placeholder="CONFIRM-EMERGENCY-PAUSE"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setConfirmDialog(null);
                  setReason('');
                  setConfirmationToken('');
                }}
                className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={() => handleEmergencyPause('activate')}
                disabled={loading || !reason || reason.length < 10 || confirmationToken !== 'CONFIRM-EMERGENCY-PAUSE'}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-neutral-300"
              >
                {loading ? 'Activating...' : 'Activate Emergency Pause'}
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmDialog === 'emergency-deactivate' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4 text-green-600">Deactivate Emergency Pause</h3>
            <p className="text-sm text-neutral-600 mb-4">
              This will resume all exclusive activations system-wide.
            </p>
            <p className="text-sm text-neutral-600 mb-2">
              Please provide a reason (minimum 10 characters):
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
                  setConfirmDialog(null);
                  setReason('');
                }}
                className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={() => handleEmergencyPause('deactivate')}
                disabled={loading || !reason || reason.length < 10}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-neutral-300"
              >
                {loading ? 'Deactivating...' : 'Deactivate Emergency Pause'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
