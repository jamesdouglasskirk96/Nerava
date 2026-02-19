/**
 * EV browser detection for frontend.
 */

export interface EVBrowserInfo {
  isEVBrowser: boolean;
  brand: string | null;
  firmwareVersion: string | null;
}

export function detectEVBrowser(): EVBrowserInfo {
  const ua = navigator.userAgent;

  // Tesla modern (2019+)
  const teslaMatch = ua.match(/Tesla\/(\d{4}\.\d+\.\d+(?:\.\d+)?)/i);
  if (teslaMatch) {
    return {
      isEVBrowser: true,
      brand: 'Tesla',
      firmwareVersion: teslaMatch[1],
    };
  }

  // Tesla legacy
  if (/QtCarBrowser/i.test(ua)) {
    return {
      isEVBrowser: true,
      brand: 'Tesla',
      firmwareVersion: 'legacy',
    };
  }

  // Android Automotive
  if (/android automotive/i.test(ua)) {
    return {
      isEVBrowser: true,
      brand: 'Android Automotive',
      firmwareVersion: null,
    };
  }

  return {
    isEVBrowser: false,
    brand: null,
    firmwareVersion: null,
  };
}

export function isTeslaBrowser(): boolean {
  const ua = navigator.userAgent;
  return /Tesla\//i.test(ua) || /QtCarBrowser/i.test(ua);
}
