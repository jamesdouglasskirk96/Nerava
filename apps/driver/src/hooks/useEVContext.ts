import { useState, useEffect } from 'react';
import { detectEVBrowser } from '../utils/evBrowserDetection';
import { api } from '../services/api';

interface ChargerInfo {
  id: string;
  name: string;
  network: string | null;
  address: string | null;
  stall_count: number | null;
}

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

interface EVContext {
  loading: boolean;
  error: string | null;

  // Browser info
  isEVBrowser: boolean;
  evBrand: string | null;
  evFirmware: string | null;

  // Location context
  atCharger: boolean;
  charger: ChargerInfo | null;

  // Recommendations
  nearbyMerchants: MerchantInfo[];

  // Fulfillment options (both are Ready on Arrival)
  fulfillmentOptions: ('ev_dine_in' | 'ev_curbside' | 'standard')[];

  // Setup
  vehicleSetupNeeded: boolean;
}

export function useEVContext(): EVContext {
  const [context, setContext] = useState<EVContext>({
    loading: true,
    error: null,
    isEVBrowser: false,
    evBrand: null,
    evFirmware: null,
    atCharger: false,
    charger: null,
    nearbyMerchants: [],
    fulfillmentOptions: ['standard'],
    vehicleSetupNeeded: false,
  });

  useEffect(() => {
    async function loadContext() {
      // First, detect browser locally
      const browserInfo = detectEVBrowser();

      try {
        // Get location
        const position = await getCurrentPosition();

        // Call backend for full context
        const response = await api.post<any>('/v1/ev-context', {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy_m: position.coords.accuracy,
        });

        setContext({
          loading: false,
          error: null,
          isEVBrowser: response.is_ev_browser,
          evBrand: response.ev_brand,
          evFirmware: response.ev_firmware,
          atCharger: response.at_charger,
          charger: response.charger,
          nearbyMerchants: response.nearby_merchants,
          fulfillmentOptions: response.fulfillment_options,
          vehicleSetupNeeded: response.vehicle_setup_needed,
        });

      } catch (error: any) {
        setContext(prev => ({
          ...prev,
          loading: false,
          error: error.message || 'Failed to load context',
          isEVBrowser: browserInfo.isEVBrowser,
          evBrand: browserInfo.brand,
          evFirmware: browserInfo.firmwareVersion,
        }));
      }
    }

    loadContext();
  }, []);

  return context;
}

function getCurrentPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 10000,
    });
  });
}
