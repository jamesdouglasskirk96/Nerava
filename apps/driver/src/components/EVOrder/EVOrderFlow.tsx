/**
 * EVOrderFlow — Order placement for EV drivers.
 *
 * Flow:
 * 1. Confirm fulfillment type (dine-in vs eat-in-car)
 * 2. Open merchant's ordering page (Toast, Square, etc.)
 * 3. Return and enter order number
 * 4. Order is QUEUED — start polling for arrival
 * 5. On arrival detection → Order RELEASED to kitchen
 * 6. Show "Order ready" notification
 */
import { useState, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { capture, DRIVER_EVENTS } from '../../analytics';
import { useArrivalPolling } from '../../hooks/useArrivalPolling';
import { openExternalUrl } from '../../utils/openExternal';

type FulfillmentType = 'ev_dine_in' | 'ev_curbside';
type Step = 'confirm' | 'ordering' | 'order_number' | 'queued' | 'released' | 'ready';

export function EVOrderFlow() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const merchantId = searchParams.get('merchant');
  const fulfillment = searchParams.get('fulfillment') as FulfillmentType;

  const [step, setStep] = useState<Step>('confirm');
  const [orderNumber, setOrderNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState<any>(null);
  const [merchant, setMerchant] = useState<any>(null);
  const [estimatedReady, setEstimatedReady] = useState<number | null>(null);

  // Start polling for arrival when order is queued
  const handleArrival = useCallback((response: any) => {
    setStep('released');
    setEstimatedReady(response.estimated_ready_minutes);

    capture(DRIVER_EVENTS.EV_ORDER_RELEASED, {
      session_id: session?.session_id,
      estimated_ready_minutes: response.estimated_ready_minutes,
    });
  }, [session]);

  const { polling } = useArrivalPolling({
    sessionId: session?.session_id || '',
    merchantLat: merchant?.lat || 0,
    merchantLng: merchant?.lng || 0,
    enabled: step === 'queued' && !!session && !!merchant,
    onArrival: handleArrival,
  });

  const handleConfirmAndOrder = async () => {
    setLoading(true);

    try {
      // Get current location
      const position = await getCurrentPosition();

      // Load merchant details for arrival detection
      const merchantResponse = await api.get<any>(`/v1/merchants/${merchantId}`);
      setMerchant(merchantResponse);

      // Create the arrival session with QUEUED status
      const response = await api.post<any>('/v1/arrival/create', {
        merchant_id: merchantId,
        arrival_type: fulfillment,
        fulfillment_type: fulfillment,
        destination_lat: merchantResponse.lat,
        destination_lng: merchantResponse.lng,
        current_lat: position.coords.latitude,
        current_lng: position.coords.longitude,
        lat: position.coords.latitude,
        lng: position.coords.longitude,
        accuracy_m: position.coords.accuracy,
      });

      setSession(response);

      capture(DRIVER_EVENTS.EV_ORDER_STARTED, {
        merchant_id: merchantId,
        fulfillment_type: fulfillment,
      });

      // Open merchant's ordering URL
      if (response.data.ordering_url) {
        openExternalUrl(response.data.ordering_url);
      }

      setStep('order_number');

    } catch (error) {
      console.error('Failed to create session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitOrderNumber = async () => {
    if (!orderNumber.trim() || !session) return;

    setLoading(true);

    try {
      // Bind order number — order remains QUEUED
      await api.put(`/v1/arrival/${session.session_id}/order`, {
        order_number: orderNumber.trim(),
      });

      // Update session queued_order_status to queued via PATCH
      // Note: The backend should set queued_order_status='queued' when order is bound
      // For now, we'll rely on backend to set this, or we can add a separate endpoint
      // The polling will handle triggering arrival when driver gets close

      capture(DRIVER_EVENTS.EV_ORDER_QUEUED, {
        session_id: session.session_id,
        fulfillment_type: fulfillment,
      });

      // Move to queued state — start polling for arrival
      setStep('queued');

    } catch (error) {
      console.error('Failed to bind order:', error);
    } finally {
      setLoading(false);
    }
  };

  // Step 1: Confirm fulfillment type
  if (step === 'confirm') {
    return (
      <div className="min-h-screen bg-white p-6">
        <div className="max-w-md mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            {fulfillment === 'ev_dine_in' ? '🍽️ Walk In & Dine' : '🚗 Eat in Car'}
          </h1>

          <div className="bg-blue-50 rounded-lg p-4 mb-6">
            {fulfillment === 'ev_dine_in' ? (
              <p className="text-blue-800">
                Your food will be <strong>hot and ready</strong> when you walk in.
                We'll notify the restaurant when you arrive.
              </p>
            ) : (
              <p className="text-blue-800">
                Stay at your car — the restaurant will <strong>bring your food
                to the charger</strong> when you arrive.
              </p>
            )}
          </div>

          <button
            onClick={handleConfirmAndOrder}
            disabled={loading}
            className="w-full py-4 bg-blue-600 text-white rounded-lg font-semibold
                       disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Continue to Order →'}
          </button>
        </div>
      </div>
    );
  }

  // Step 2: Enter order number after ordering
  if (step === 'order_number') {
    return (
      <div className="min-h-screen bg-white p-6">
        <div className="max-w-md mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Almost done!
          </h1>
          <p className="text-gray-600 mb-6">
            Enter your order number from the receipt.
          </p>

          <input
            type="text"
            value={orderNumber}
            onChange={(e) => setOrderNumber(e.target.value)}
            placeholder="Order #"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg text-lg
                       mb-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />

          <button
            onClick={handleSubmitOrderNumber}
            disabled={!orderNumber.trim() || loading}
            className="w-full py-4 bg-blue-600 text-white rounded-lg font-semibold
                       disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'Queue My Order'}
          </button>

          <button
            onClick={() => session?.ordering_url && openExternalUrl(session.ordering_url)}
            className="w-full py-3 text-blue-600 mt-4"
          >
            Open menu again
          </button>
        </div>
      </div>
    );
  }

  // Step 3: Order queued, waiting for arrival
  if (step === 'queued') {
    return (
      <div className="min-h-screen bg-white p-6">
        <div className="max-w-md mx-auto text-center">
          <div className="text-6xl mb-4">🚗</div>

          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Order Queued
          </h1>

          <p className="text-gray-600 mb-6">
            Drive to <strong>{merchant?.name}</strong>.
            <br />
            We'll release your order when you arrive.
          </p>

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="text-sm text-gray-500">Order</div>
            <div className="text-xl font-bold mb-2">#{orderNumber}</div>

            <div className="flex items-center justify-center gap-2 text-sm text-blue-600">
              {polling && (
                <>
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                  <span>Detecting arrival...</span>
                </>
              )}
            </div>
          </div>

          <div className="bg-yellow-50 rounded-lg p-4 text-sm text-yellow-800">
            <strong>Keep this browser open</strong> while you drive.
            We'll detect when you arrive.
          </div>
        </div>
      </div>
    );
  }

  // Step 4: Order released to kitchen
  if (step === 'released') {
    return (
      <div className="min-h-screen bg-white p-6">
        <div className="max-w-md mx-auto text-center">
          <div className="text-6xl mb-4">✅</div>

          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Order Sent!
          </h1>

          <p className="text-gray-600 mb-6">
            {fulfillment === 'ev_dine_in' ? (
              <>
                Your food is being prepared.
                <br />
                Head to <strong>{merchant?.name}</strong> now!
              </>
            ) : (
              <>
                Your food is being prepared.
                <br />
                Stay at your car — they'll bring it to you.
              </>
            )}
          </p>

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="text-sm text-gray-500">Order #{orderNumber}</div>
            {estimatedReady && (
              <div className="text-lg font-semibold text-green-600 mt-1">
                Ready in ~{estimatedReady} minutes
              </div>
            )}
          </div>

          <button
            onClick={() => navigate('/')}
            className="w-full py-4 bg-gray-100 text-gray-700 rounded-lg font-semibold"
          >
            Done
          </button>
        </div>
      </div>
    );
  }

  return null;
}

function getCurrentPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 10000,
    });
  });
}
