import { useEffect } from 'react';
import type { ArrivalSession } from '../../services/arrival';
import { getStoredSessionToken } from '../../services/arrival';
import { useArrivalLocationPolling } from '../../hooks/useArrivalLocationPolling';
import { Button } from '../shared/Button';

interface Props {
  session: ArrivalSession;
  onArrived: (promoCode: string, expiresAt: string) => void;
}

export function GoToMerchantScreen({ session, onArrived }: Props) {
  const token = getStoredSessionToken();
  const pollingResult = useArrivalLocationPolling(token, true);

  useEffect(() => {
    if (pollingResult.arrived && pollingResult.promo_code && pollingResult.promo_code_expires_at) {
      onArrived(pollingResult.promo_code, pollingResult.promo_code_expires_at);
    }
  }, [pollingResult.arrived, pollingResult.promo_code, pollingResult.promo_code_expires_at, onArrived]);

  const merchant = session.merchant;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-white">
      <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-2 mb-6">
        <div className="flex items-center space-x-2 text-green-700">
          <span className="text-xl">✓</span>
          <span className="font-semibold">EV Verified</span>
        </div>
      </div>

      <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">
        Head to {merchant.name}
      </h1>

      <p className="text-gray-600 mb-6 text-center">{merchant.address}</p>

      {pollingResult.distance_m !== undefined && (
        <div className="text-2xl font-semibold text-gray-900 mb-6">
          {pollingResult.distance_m < 1000
            ? `${pollingResult.distance_m}m away`
            : `${(pollingResult.distance_m / 1000).toFixed(1)}km away`}
        </div>
      )}

      <div className="flex flex-col items-center mb-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-3"></div>
        <p className="text-gray-600 text-center">
          Your charging credit will unlock when you arrive
        </p>
      </div>

      {merchant.lat && merchant.lng && (
        <a
          href={`https://maps.google.com/?daddr=${merchant.lat},${merchant.lng}`}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full max-w-md"
        >
          <Button variant="secondary" className="w-full">
            Get Directions
          </Button>
        </a>
      )}

      {pollingResult.error && (
        <div className="mt-4 text-red-600 text-sm text-center">
          {pollingResult.error}
        </div>
      )}
    </div>
  );
}
