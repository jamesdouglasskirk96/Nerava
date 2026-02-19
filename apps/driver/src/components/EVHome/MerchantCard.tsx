// React import removed - JSX transform doesn't require it
import { useNavigate } from 'react-router-dom';

interface MerchantInfo {
  id: string;
  name: string;
  category: string | null;
  rating: number | null;
  photo_url: string | null;
  distance_m: number;
  walk_minutes: number;
  ordering_url: string | null;
}

interface MerchantCardProps {
  merchant: MerchantInfo;
  fulfillmentOptions: ('ev_dine_in' | 'ev_curbside' | 'standard')[];
}

export function MerchantCard({ merchant, fulfillmentOptions }: MerchantCardProps) {
  const navigate = useNavigate();

  const handleOrder = (fulfillment: string) => {
    navigate(`/ev-order?merchant=${merchant.id}&fulfillment=${fulfillment}`);
  };

  const showEVOptions = fulfillmentOptions.includes('ev_dine_in') || fulfillmentOptions.includes('ev_curbside');

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      {/* Photo */}
      {merchant.photo_url && (
        <img
          src={merchant.photo_url}
          alt={merchant.name}
          className="w-full h-32 object-cover"
        />
      )}

      <div className="p-4">
        {/* Name and rating */}
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-semibold text-gray-900">
            {merchant.name}
          </h3>
          {merchant.rating && (
            <span className="text-sm text-gray-600">
              ★ {merchant.rating.toFixed(1)}
            </span>
          )}
        </div>

        {/* Category and distance */}
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
          {merchant.category && <span>{merchant.category}</span>}
          <span>·</span>
          <span>{merchant.walk_minutes} min walk</span>
        </div>

        {/* Fulfillment options — both are Ready on Arrival */}
        {showEVOptions ? (
          <div className="space-y-2">
            <button
              onClick={() => handleOrder('ev_dine_in')}
              className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg
                         font-medium hover:bg-blue-700 transition-colors"
            >
              🍽️ Walk In & Dine
            </button>
            <button
              onClick={() => handleOrder('ev_curbside')}
              className="w-full py-3 px-4 bg-white text-blue-600 border-2 border-blue-600
                         rounded-lg font-medium hover:bg-blue-50 transition-colors"
            >
              🚗 Eat in Car
            </button>
          </div>
        ) : (
          <button
            onClick={() => handleOrder('standard')}
            className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg
                       font-medium hover:bg-blue-700 transition-colors"
          >
            Order Now →
          </button>
        )}
      </div>
    </div>
  );
}
