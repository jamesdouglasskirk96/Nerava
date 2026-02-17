/**
 * TeslaConnect — Connect Tesla account and verify charging status.
 *
 * Provides an alternative to car-browser verification by connecting
 * directly to Tesla Fleet API to verify charging status.
 */
import { useState, useEffect } from 'react';
import { Button } from '../shared/Button';
import { api } from '../../services/api';

interface TeslaConnectionStatus {
  connected: boolean;
  vehicle_name?: string;
  vehicle_model?: string;
  vin?: string;
}

interface TeslaConnectResponse {
  authorization_url: string;
  state: string;
}

interface VerifyChargingResponse {
  is_charging: boolean;
  battery_level?: number;
  charge_rate_kw?: number;
  ev_code?: string;
  message: string;
}

interface Props {
  merchantPlaceId?: string;
  merchantName?: string;
  chargerId?: string;
  onCodeGenerated?: (code: string) => void;
}

export function TeslaConnect({ merchantPlaceId, merchantName, chargerId, onCodeGenerated }: Props) {
  const [status, setStatus] = useState<TeslaConnectionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<VerifyChargingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Check connection status on mount
  useEffect(() => {
    checkConnectionStatus();
  }, []);

  const checkConnectionStatus = async () => {
    try {
      const response = await api.get<TeslaConnectionStatus>('/v1/auth/tesla/status');
      setStatus(response);
    } catch (e) {
      console.error('Failed to check Tesla status:', e);
      setStatus({ connected: false });
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    setError(null);
    setLoading(true);

    try {
      const response = await api.get<TeslaConnectResponse>('/v1/auth/tesla/connect');
      // Redirect to Tesla OAuth
      window.location.href = response.authorization_url;
    } catch (e) {
      setError('Failed to start Tesla connection. Please try again.');
      setLoading(false);
    }
  };

  const handleVerifyCharging = async () => {
    setError(null);
    setVerifying(true);

    try {
      const response = await api.post<VerifyChargingResponse>('/v1/auth/tesla/verify-charging', {
        merchant_place_id: merchantPlaceId,
        merchant_name: merchantName,
        charger_id: chargerId,
      });

      setVerifyResult(response);

      if (response.ev_code && onCodeGenerated) {
        onCodeGenerated(response.ev_code);
      }
    } catch (e) {
      setError('Failed to verify charging status. Please try again.');
    } finally {
      setVerifying(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await api.post('/v1/auth/tesla/disconnect', {});
      setStatus({ connected: false });
      setVerifyResult(null);
    } catch (e) {
      console.error('Failed to disconnect:', e);
    }
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      </div>
    );
  }

  // Show EV code if generated
  if (verifyResult?.ev_code) {
    return (
      <div className="p-6 bg-gradient-to-b from-green-50 to-white rounded-xl border border-green-200">
        <div className="text-center">
          <div className="text-5xl mb-4">⚡</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Charging Verified!</h2>
          <p className="text-gray-600 mb-6">{verifyResult.message}</p>

          {/* EV Code Display */}
          <div className="bg-white rounded-2xl border-2 border-blue-500 p-6 mb-6">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Your EV Code</p>
            <p className="text-4xl font-mono font-bold text-blue-600 tracking-wider">
              {verifyResult.ev_code}
            </p>
          </div>

          {verifyResult.battery_level && (
            <div className="flex items-center justify-center gap-4 text-sm text-gray-600">
              <span>🔋 {verifyResult.battery_level}%</span>
              {verifyResult.charge_rate_kw && (
                <span>⚡ {verifyResult.charge_rate_kw} kW</span>
              )}
            </div>
          )}

          <p className="text-sm text-gray-500 mt-6">
            Show this code to the merchant to redeem your reward
          </p>
        </div>
      </div>
    );
  }

  // Connected state - show verify button
  if (status?.connected) {
    return (
      <div className="p-6 bg-white rounded-xl border border-gray-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-red-600" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 18.5L4 16V8.5l8 4 8-4V16l-8 4.5z"/>
            </svg>
          </div>
          <div>
            <p className="font-semibold text-gray-900">
              {status.vehicle_name || 'Tesla'}
            </p>
            <p className="text-sm text-gray-500">
              {status.vehicle_model} • ••••{status.vin}
            </p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 text-sm p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {verifyResult && !verifyResult.is_charging && (
          <div className="bg-yellow-50 text-yellow-800 text-sm p-3 rounded-lg mb-4">
            {verifyResult.message}
          </div>
        )}

        <Button
          onClick={handleVerifyCharging}
          disabled={verifying}
          className="w-full mb-3"
        >
          {verifying ? 'Verifying...' : 'Verify Charging & Get Code'}
        </Button>

        <button
          onClick={handleDisconnect}
          className="w-full text-sm text-gray-500 hover:text-gray-700"
        >
          Disconnect Tesla
        </button>
      </div>
    );
  }

  // Not connected - show connect button
  return (
    <div className="p-6 bg-white rounded-xl border border-gray-200">
      <div className="text-center mb-6">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-600" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 18.5L4 16V8.5l8 4 8-4V16l-8 4.5z"/>
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Connect Your Tesla
        </h3>
        <p className="text-sm text-gray-600">
          Link your Tesla account to automatically verify your charging session
          and unlock exclusive EV rewards.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 text-sm p-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      <Button onClick={handleConnect} className="w-full">
        <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2L2 7v10l10 5 10-5V7L12 2z"/>
        </svg>
        Connect Tesla Account
      </Button>

      <p className="text-xs text-gray-400 text-center mt-4">
        We only access your charging status. Your data is secure.
      </p>
    </div>
  );
}
