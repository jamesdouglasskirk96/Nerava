import { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { usePageVisibility } from './usePageVisibility';

interface UseArrivalPollingOptions {
  sessionId: string;
  merchantLat: number;
  merchantLng: number;
  enabled: boolean;
  onArrival: (response: ArrivalResponse) => void;
}

interface ArrivalResponse {
  status: string;
  order_released: boolean;
  estimated_ready_minutes?: number;
}

export function useArrivalPolling({
  sessionId,
  merchantLat,
  merchantLng,
  enabled,
  onArrival,
}: UseArrivalPollingOptions) {
  const [polling, setPolling] = useState(false);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isVisible = usePageVisibility();

  useEffect(() => {
    if (!enabled || !isVisible) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (!enabled) setPolling(false);
      return;
    }

    setPolling(true);

    const checkArrival = async () => {
      try {
        // Try to get location (fails while driving, succeeds when parked)
        const position = await new Promise<GeolocationPosition>(
          (resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
              resolve,
              reject,
              { enableHighAccuracy: true, timeout: 10000 }
            );
          }
        );

        setLastCheck(new Date());

        // Calculate distance to restaurant
        const distance = haversine(
          position.coords.latitude,
          position.coords.longitude,
          merchantLat,
          merchantLng
        );

        console.log(`Distance to restaurant: ${distance}m`);

        // If within 500m, trigger arrival
        if (distance < 500) {
          const response = await api.post<any>(
            `/v1/arrival/${sessionId}/trigger-arrival`,
            {
              lat: position.coords.latitude,
              lng: position.coords.longitude,
              accuracy_m: position.coords.accuracy,
            }
          );

          if (response.order_released) {
            setPolling(false);
            if (intervalRef.current) clearInterval(intervalRef.current);
            onArrival(response);
          }
        }

      } catch (error) {
        // Geolocation failed — probably still driving
        // This is expected behavior, keep polling
        console.log('Still driving, geolocation unavailable...');
        setLastCheck(new Date());
      }
    };

    // Poll every 30 seconds
    checkArrival(); // Check immediately
    intervalRef.current = setInterval(checkArrival, 30000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [sessionId, merchantLat, merchantLng, enabled, onArrival, isVisible]);

  return { polling, lastCheck };
}

// Haversine formula for distance calculation
function haversine(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000; // Earth's radius in meters
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function toRad(deg: number): number {
  return deg * (Math.PI / 180);
}
