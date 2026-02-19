/**
 * EVHome — Optimized experience for Tesla browser users at chargers.
 */
// React import removed - JSX transform doesn't require it
import { useEVContext } from '../../hooks/useEVContext';
import { MerchantCard } from './MerchantCard';
import { VehicleSetupPrompt } from './VehicleSetupPrompt';

export function EVHome() {
  const context = useEVContext();

  if (context.loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Show vehicle setup if needed (first time EV browser user)
  if (context.vehicleSetupNeeded) {
    return <VehicleSetupPrompt onComplete={() => window.location.reload()} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with charger info */}
      {context.atCharger && context.charger && (
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">⚡</span>
            <span className="text-sm font-medium opacity-90">
              Charging at
            </span>
          </div>
          <h1 className="text-xl font-semibold">
            {context.charger.name}
          </h1>
          {context.charger.address && (
            <p className="text-sm opacity-80 mt-1">
              {context.charger.address}
            </p>
          )}
        </div>
      )}

      {/* Value proposition */}
      <div className="px-4 py-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Hot food, ready on arrival
        </h2>
        <p className="text-sm text-gray-600">
          Order now — your food will be ready when you walk in,
          or we'll bring it to your car.
        </p>
      </div>

      {/* Merchant list */}
      <div className="px-4 space-y-4 pb-8">
        {context.nearbyMerchants.map((merchant) => (
          <MerchantCard
            key={merchant.id}
            merchant={merchant}
            fulfillmentOptions={context.fulfillmentOptions}
          />
        ))}

        {context.nearbyMerchants.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No nearby restaurants found
          </div>
        )}
      </div>
    </div>
  );
}
