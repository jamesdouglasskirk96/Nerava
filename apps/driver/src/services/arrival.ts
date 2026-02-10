const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '';

export interface Merchant {
  id: string;
  name: string;
  logo_url?: string;
  offer?: string;
  address?: string;
  lat?: number;
  lng?: number;
  geofence_radius_m?: number;
}

export interface ArrivalSession {
  session_id: string;
  session_token: string;
  state: 'pending' | 'car_verified' | 'arrived' | 'redeemed' | 'expired';
  merchant: Merchant;
  promo_code?: string;
  promo_code_expires_at?: string;
  expires_at?: string;
}

const SESSION_TOKEN_KEY = 'nerava_arrival_session_token';

export function getStoredSessionToken(): string | null {
  return localStorage.getItem(SESSION_TOKEN_KEY);
}

export function storeSessionToken(token: string): void {
  localStorage.setItem(SESSION_TOKEN_KEY, token);
}

export function clearSessionToken(): void {
  localStorage.removeItem(SESSION_TOKEN_KEY);
}

export async function startSession(merchantId: string): Promise<ArrivalSession> {
  const response = await fetch(`${API_BASE}/v1/arrival/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ merchant_id: merchantId }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to start session' }));
    throw new Error(error.detail || 'Failed to start session');
  }

  const data = await response.json();
  storeSessionToken(data.session_token);
  return data;
}

export async function verifyPin(sessionToken: string, pin: string): Promise<ArrivalSession> {
  const response = await fetch(`${API_BASE}/v1/arrival/verify-pin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_token: sessionToken, pin }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Invalid code');
  }

  return response.json();
}

export async function checkLocation(
  sessionToken: string,
  lat: number,
  lng: number
): Promise<{ arrived: boolean; distance_m?: number; promo_code?: string; promo_code_expires_at?: string; message?: string }> {
  const response = await fetch(`${API_BASE}/v1/arrival/check-location`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_token: sessionToken, lat, lng }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to check location' }));
    throw new Error(error.detail || 'Failed to check location');
  }

  return response.json();
}

export async function getSessionStatus(sessionToken: string): Promise<ArrivalSession | null> {
  const response = await fetch(`${API_BASE}/v1/arrival/status?session_token=${encodeURIComponent(sessionToken)}`);

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get session status' }));
    throw new Error(error.detail || 'Failed to get session status');
  }

  return response.json();
}
