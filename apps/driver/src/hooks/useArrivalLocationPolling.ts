import { useEffect, useRef, useState } from 'react';
import { checkLocation } from '../services/arrival';

interface PollingResult {
  arrived: boolean;
  distance_m?: number;
  promo_code?: string;
  promo_code_expires_at?: string;
  error?: string;
}

export function useArrivalLocationPolling(
  sessionToken: string | null,
  isActive: boolean,
  intervalMs: number = 10000
): PollingResult {
  const [result, setResult] = useState<PollingResult>({ arrived: false });
  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (!sessionToken || !isActive) {
      return;
    }

    const poll = async () => {
      try {
        const position = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 10000,
          });
        });

        const response = await checkLocation(
          sessionToken,
          position.coords.latitude,
          position.coords.longitude
        );

        setResult({
          arrived: response.arrived,
          distance_m: response.distance_m,
          promo_code: response.promo_code,
          promo_code_expires_at: response.promo_code_expires_at,
        });
      } catch (error) {
        setResult(prev => ({ ...prev, error: String(error) }));
      }
    };

    // Poll immediately, then on interval
    poll();
    intervalRef.current = window.setInterval(poll, intervalMs);

    // Also poll on visibility change (app comes back to foreground)
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        poll();
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);

    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current);
      }
      document.removeEventListener('visibilitychange', handleVisibility);
    };
  }, [sessionToken, isActive, intervalMs]);

  return result;
}
