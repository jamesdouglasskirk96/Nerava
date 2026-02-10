import { useEffect, useState } from 'react';
import type { Merchant } from '../../services/arrival';
import { Button } from '../shared/Button';

interface Props {
  merchantId: string;
  onCheckIn: () => void;
}

const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '';

export function CheckInPrompt({ merchantId, onCheckIn }: Props) {
  const [merchant, setMerchant] = useState<Merchant | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch merchant info for display
    async function fetchMerchant() {
      try {
        const response = await fetch(`${API_BASE}/v1/merchants/${merchantId}`);
        if (response.ok) {
          const data = await response.json();
          setMerchant({
            id: data.id || merchantId,
            name: data.name || 'Merchant',
            logo_url: data.logo_url,
            offer: data.ev_offer_text || '$5 charging credit',
            address: data.address,
          });
        }
      } catch (error) {
        console.error('Failed to fetch merchant:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchMerchant();
  }, [merchantId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Loading merchant...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-white">
      {merchant?.logo_url && (
        <img
          src={merchant.logo_url}
          alt={merchant.name}
          className="w-24 h-24 rounded-lg mb-6 object-contain"
        />
      )}

      <h1 className="text-3xl font-bold text-gray-900 mb-4 text-center">
        {merchant?.name || 'Merchant'}
      </h1>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 w-full max-w-md">
        <div className="text-sm text-blue-600 font-medium mb-1">EV Driver Offer</div>
        <div className="text-2xl font-bold text-blue-900">
          {merchant?.offer || '$5 charging credit'}
        </div>
      </div>

      <p className="text-gray-600 mb-8 text-center max-w-md">
        Verify your EV arrival to unlock your charging credit
      </p>

      <Button onClick={onCheckIn} className="w-full max-w-md">
        Check In
      </Button>
    </div>
  );
}
