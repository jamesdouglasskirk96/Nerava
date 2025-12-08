// Determine API base URL based on environment
function getApiBase() {
  // Check for explicit override in localStorage
  if (localStorage.NERAVA_URL) {
    return localStorage.NERAVA_URL;
  }
  
  // Check for Vite environment variable (if using Vite)
  try {
    // eslint-disable-next-line no-undef
    if (import.meta && import.meta.env && import.meta.env.VITE_API_BASE_URL) {
      // eslint-disable-next-line no-undef
      return import.meta.env.VITE_API_BASE_URL;
    }
  } catch (e) {
    // import.meta not available (not in ES module context or browser doesn't support it)
  }
  
  // Detect production environment
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.includes('192.168.') || hostname.includes('10.');
  const isVercel = hostname.includes('vercel.app');
  const isNeravaNetwork = hostname.includes('nerava.network');
  const isProduction = !isLocalhost && (protocol === 'https:' || isVercel || isNeravaNetwork);
  
  console.log('[API] Detected environment:', { hostname, protocol, isLocalhost, isVercel, isNeravaNetwork, isProduction });
  
  // Development: check for explicit production backend override (full URL)
  // This allows local UI to call production backend for testing
  // Example: localStorage.setItem('NERAVA_PROD_BACKEND', 'https://web-production-526f6.up.railway.app')
  const prodBackendOverride = localStorage.getItem('NERAVA_PROD_BACKEND');
  if (prodBackendOverride && prodBackendOverride.startsWith('http')) {
    console.log('[API] Using production backend (override URL):', prodBackendOverride);
    return prodBackendOverride;
  }
  
  // Production: use Railway backend (current production deployment)
  if (isProduction) {
    const prodUrl = 'https://web-production-526f6.up.railway.app';
    console.log('[API] Using production backend (Railway):', prodUrl);
    return prodUrl;
  }
  
  // Development: use same origin as frontend to avoid CORS issues
  // This ensures requests from localhost:8001 go to localhost:8001, not 127.0.0.1:8001
  const devUrl = window.location.origin; // e.g., "http://localhost:8001"
  console.log('[API] Using development backend (same origin):', devUrl);
  return devUrl;
}

const BASE = getApiBase();

// Constants for Domain January charge party
export const EVENT_SLUG = 'domain_jan_2025';
export const ZONE_SLUG = 'domain_austin';

async function _req(path, opts = {}) {
  const headers = { 
    Accept: 'application/json',
    'Content-Type': 'application/json',
    ...opts.headers 
  };
  
  const r = await fetch(BASE + path, {
    headers,
    credentials: 'include',
    ...opts,
  });
  
  if (r.status === 404) return null;
  if (!r.ok) {
    const errorText = await r.text().catch(() => 'Unknown error');
    throw new Error(`${r.status} ${path}: ${errorText}`);
  }
  return r.json();
}

export const apiGet = (path, params) => {
  const url = new URL(BASE + path);
  Object.entries(params || {}).forEach(([k, v]) => url.searchParams.set(k, v));
  return _req(url.pathname + url.search);
};

export async function apiPost(path, body = {}, headers = {}) {
  return _req(path, { 
    method: 'POST', 
    body: typeof body === 'string' ? body : JSON.stringify(body),
    headers 
  });
}

// ============================================
// Auth API (canonical /v1/auth/*)
// ============================================

/**
 * Register a new user
 */
export async function apiRegister(email, password, displayName = null, role = 'driver') {
  try {
    const body = { email, password };
    if (displayName) body.display_name = displayName;
    if (role) body.role = role;
    
    const res = await _req('/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(body),
    });
    
    console.log('[API][Auth] Registration successful:', email);
    
    // Store token if provided
    if (res.access_token) {
      // Token is in HTTP-only cookie, but store user info if available
      await apiMe(); // Refresh current user
    }
    
    return res;
  } catch (e) {
    console.error('[API][Auth] Registration failed:', e.message);
    throw e;
  }
}

/**
 * Login user
 */
export async function apiLogin(email, password) {
  try {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const res = await _req('/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });
    
    console.log('[API][Auth] Login successful:', email);
    
    // Token is in HTTP-only cookie, refresh current user
    const user = await apiMe();
    return { ...res, user };
  } catch (e) {
    console.error('[API][Auth] Login failed:', e.message);
    throw e;
  }
}

/**
 * Request magic link for email-only authentication
 */
export async function apiRequestMagicLink(email) {
  try {
    const res = await _req('/v1/auth/magic_link/request', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
    
    console.log('[Auth][MagicLink] Request sent for:', email);
    return res;
  } catch (e) {
    console.error('[Auth][MagicLink] Request failed:', e.message);
    throw e;
  }
}

/**
 * Verify magic link token and create session
 */
export async function apiVerifyMagicLink(token) {
  try {
    const res = await _req('/v1/auth/magic_link/verify', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
    
    console.log('[Auth][MagicLink] Verify success');
    
    // Token is in HTTP-only cookie, refresh current user
    const user = await apiMe();
    return { ...res, user };
  } catch (e) {
    console.error('[Auth][MagicLink] Verify failed:', e.message);
    throw e;
  }
}

/**
 * Get Smartcar Connect URL for EV integration
 */
export async function apiGetSmartcarConnectUrl() {
  try {
    const res = await _req('/v1/ev/connect', {
      method: 'GET',
    });
    return res;
  } catch (e) {
    console.error('[API][Smartcar] Failed to get connect URL:', e.message);
    throw e;
  }
}

/**
 * Get latest vehicle telemetry
 */
export async function apiGetVehicleTelemetry() {
  try {
    const res = await _req('/v1/ev/me/telemetry/latest', {
      method: 'GET',
    });
    return res;
  } catch (e) {
    console.error('[API][Smartcar] Failed to get telemetry:', e.message);
    throw e;
  }
}

/**
 * Logout user
 */
export async function apiLogout() {
  try {
    await _req('/v1/auth/logout', { method: 'POST' });
    console.log('[API][Auth] Logged out');
    
    // Clear local user state
    if (typeof window !== 'undefined') {
      window.NERAVA_USER = null;
      localStorage.removeItem('NERAVA_USER_ID');
    }
  } catch (e) {
    console.warn('[API][Auth] Logout failed:', e.message);
    // Clear local state anyway
    if (typeof window !== 'undefined') {
      window.NERAVA_USER = null;
      localStorage.removeItem('NERAVA_USER_ID');
    }
  }
}

/**
 * Get current user info
 */
export async function apiMe() {
  try {
    const user = await _req('/v1/auth/me');
    
    // Store globally
    if (typeof window !== 'undefined') {
      window.NERAVA_USER = user;
      if (user.id) {
        localStorage.setItem('NERAVA_USER_ID', String(user.id));
      }
    }
    
    return user;
  } catch (e) {
    // 401 means not logged in - that's OK
    if (e.message.includes('401') || e.message.includes('Unauthorized')) {
      if (typeof window !== 'undefined') {
        window.NERAVA_USER = null;
        localStorage.removeItem('NERAVA_USER_ID');
      }
      return null;
    }
    console.error('[API][Auth] Failed to get current user:', e.message);
    throw e;
  }
}

/**
 * Get current user (from cache or fetch)
 */
export function getCurrentUser() {
  if (typeof window !== 'undefined' && window.NERAVA_USER) {
    return window.NERAVA_USER;
  }
  
  // Try to get from localStorage
  const userId = localStorage.getItem('NERAVA_USER_ID');
  if (userId) {
    // Return minimal user object - will be refreshed on next apiMe() call
    return { id: parseInt(userId, 10) };
  }
  
  return null;
}

export async function fetchPilotBootstrap() {
  const res = await fetch(`${BASE}/v1/pilot/app/bootstrap`, {
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error(`Pilot bootstrap failed (${res.status})`);
  }
  return res.json();
}

export async function fetchPilotWhileYouCharge(sessionId) {
  const url = new URL(`${BASE}/v1/pilot/while_you_charge`);
  if (sessionId) {
    url.searchParams.set('session_id', sessionId);
  }
  console.log('[API] Fetching while_you_charge from:', url.toString());
  try {
    const res = await fetch(url.toString(), { credentials: 'include' });
    console.log('[API] While you charge response status:', res.status, res.statusText);
    if (!res.ok) {
      const errorText = await res.text();
      console.error('[API] While you charge error response:', errorText);
      throw new Error(`Pilot while-you-charge failed (${res.status}): ${errorText}`);
    }
    const data = await res.json();
    console.log('[API] While you charge data:', data);
    return data;
  } catch (err) {
    console.error('[API] While you charge fetch error:', err);
    throw err;
  }
}

export async function fetchMerchantOffer(merchantId, amountCents = 500) {
  const res = await fetch(`${BASE}/v1/pilot/merchant_offer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      merchant_id: merchantId,
      amount_cents: amountCents
    })
  });
  if (!res.ok) {
    throw new Error(`Failed to create merchant offer (${res.status})`);
  }
  return res.json();
}

export async function pilotStartSession(userLat, userLng, chargerId = null, merchantId = null, userId = 123) {
  const res = await fetch(`${BASE}/v1/pilot/start_session?user_id=${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      user_lat: userLat,
      user_lng: userLng,
      charger_id: chargerId,
      merchant_id: merchantId
    })
  });
  if (!res.ok) {
    throw new Error(`Failed to start session (${res.status})`);
  }
  return res.json();
}

export async function pilotVerifyPing(sessionId, userLat, userLng) {
  const res = await fetch(`${BASE}/v1/pilot/verify_ping`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      session_id: sessionId,
      user_lat: userLat,
      user_lng: userLng
    })
  });
  if (!res.ok) {
    throw new Error(`Failed to verify ping (${res.status})`);
  }
  const rawData = await res.json();
  
  // Normalize response to ensure consistent field names
  // Backend returns: distance_to_charger_m, dwell_seconds, needed_seconds (only if not verified), etc.
  return {
    session_id: sessionId,
    verified: rawData.verified || false,
    verified_at_charger: rawData.verified_at_charger || false,
    reward_earned: rawData.reward_earned || false,
    ready_to_claim: rawData.ready_to_claim || false,
    charger_radius_m: rawData.charger_radius_m || 60,
    distance_to_charger_m: rawData.distance_to_charger_m ?? rawData.distance_m ?? 0,
    dwell_seconds: rawData.dwell_seconds || 0,
    needed_seconds: rawData.needed_seconds ?? (rawData.dwell_required_s ? rawData.dwell_required_s - (rawData.dwell_seconds || 0) : 180),
    nova_awarded: rawData.nova_awarded || 0,
    wallet_balance: rawData.wallet_balance || 0,
    wallet_balance_nova: rawData.wallet_balance_nova || 0,
    distance_to_merchant_m: rawData.distance_to_merchant_m,
    within_merchant_radius: rawData.within_merchant_radius || false,
    verification_score: rawData.verification_score || 0,
    // Pass through any other fields
    ...rawData
  };
}

export async function pilotVerifyVisit(sessionId, merchantId, userLat, userLng) {
  const res = await fetch(`${BASE}/v1/pilot/verify_visit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      session_id: sessionId,
      merchant_id: merchantId,
      user_lat: userLat,
      user_lng: userLng
    })
  });
  if (!res.ok) {
    throw new Error(`Failed to verify visit (${res.status})`);
  }
  return res.json();
}

export async function pilotCancelSession(sessionId) {
  try {
    const res = await fetch(`${BASE}/v1/pilot/session/cancel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        session_id: sessionId
      })
    });
    // Return result even if not 200 - idempotent endpoint
    // 404 means endpoint not deployed yet - that's OK, cleanup still happens
    if (!res.ok && res.status !== 404) {
      console.warn(`[API] Cancel session returned ${res.status}`);
    }
    return res.json().catch(() => ({ ok: true })); // Return safe default if JSON parse fails
  } catch (e) {
    // Network errors or 404 (endpoint not deployed) - return success to allow cleanup
    return { ok: true };
  }
}

// ============================================
// Driver API (canonical /v1/drivers/*)
// ============================================

/**
 * Join a charge party event
 */
export async function apiJoinChargeEvent({ eventSlug, chargerId = null, merchantId = null, userLat = null, userLng = null }) {
  try {
    const body = {};
    if (chargerId) body.charger_id = chargerId;
    if (merchantId) body.merchant_id = merchantId;
    if (userLat !== null) body.user_lat = userLat;
    if (userLng !== null) body.user_lng = userLng;
    
    const res = await _req(`/v1/drivers/charge_events/${encodeURIComponent(eventSlug)}/join`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
    
    console.log('[API][Drivers] Joined charge event (v1):', eventSlug, res);
    return res;
  } catch (e) {
    console.error('[API][Drivers] Failed to join charge event:', e.message);
    throw e;
  }
}

/**
 * Get nearby merchants in a zone
 */
export async function apiNearbyMerchants({ lat, lng, zoneSlug, radiusM = 5000 }) {
  try {
    const params = new URLSearchParams({
      lat: String(lat),
      lng: String(lng),
      zone_slug: zoneSlug,
      radius_m: String(radiusM),
    });
    
    const res = await _req(`/v1/drivers/merchants/nearby?${params.toString()}`);
    console.log('[API][Drivers] Nearby merchants:', res?.length || 0);
    return res || [];
  } catch (e) {
    console.error('[API][Drivers] Failed to get nearby merchants:', e.message);
    return []; // Return empty array on error
  }
}

/**
 * Get driver wallet
 */
export async function apiDriverWallet() {
  try {
    const res = await _req('/v1/drivers/me/wallet');
    console.log('[API][Drivers] Wallet:', res);
    return res;
  } catch (e) {
    console.error('[API][Drivers] Failed to get wallet:', e.message);
    throw e;
  }
}

/**
 * Get driver activity/transactions
 */
export async function apiDriverActivity({ limit = 50 } = {}) {
  try {
    const params = new URLSearchParams({ limit: String(limit) });
    const res = await _req(`/v1/drivers/activity?${params.toString()}`);
    console.log('[API][Drivers] Activity (v1):', res);
    
    // Backend returns array directly, or wrap if needed
    const events = Array.isArray(res) ? res : (res.events || res.transactions || []);
    return events;
  } catch (e) {
    console.warn('[API][Drivers] Failed to get activity:', e.message);
    return [];
  }
}

/**
 * Session ping (update session location)
 * Canonical v1 endpoint - /v1/drivers/sessions/{id}/ping
 */
export async function apiSessionPing({ sessionId, lat, lng, location }) {
  // Support both { lat, lng } and { location: { lat, lng } } formats
  const finalLat = lat ?? location?.lat;
  const finalLng = lng ?? location?.lng;
  
  if (finalLat === undefined || finalLng === undefined) {
    throw new Error('apiSessionPing requires lat and lng');
  }
  try {
    const res = await _req(`/v1/drivers/sessions/${encodeURIComponent(sessionId)}/ping`, {
      method: 'POST',
      body: JSON.stringify({ lat: finalLat, lng: finalLng }),
    });
    console.log('[API][Drivers] Session ping (v1):', res);
    
    // Normalize response to match expected shape
    return {
      session_id: sessionId,
      verified: res.verified || false,
      verified_at_charger: res.verified_at_charger || false,
      reward_earned: res.reward_earned || false,
      ready_to_claim: res.ready_to_claim || false,
      charger_radius_m: res.charger_radius_m || 60,
      distance_to_charger_m: res.distance_to_charger_m ?? 0,
      dwell_seconds: res.dwell_seconds || 0,
      needed_seconds: res.needed_seconds ?? 0,
      nova_awarded: res.nova_awarded || 0,
      wallet_balance: 0,
      wallet_balance_nova: res.wallet_balance_nova || 0,
      distance_to_merchant_m: res.distance_to_merchant_m,
      within_merchant_radius: res.within_merchant_radius || false,
      verification_score: res.verification_score || 0,
      ...res
    };
  } catch (e) {
    console.error('[API][Drivers] Session ping (v1) failed:', e.message);
    throw e;
  }
}

/**
 * Cancel session
 * Canonical v1 endpoint - /v1/drivers/sessions/{id}/cancel
 */
export async function apiCancelSession(sessionId) {
  try {
    const res = await fetch(`${BASE}/v1/drivers/sessions/${encodeURIComponent(sessionId)}/cancel`, {
      method: 'POST',
      credentials: 'include',
    });
    
    // 204 No Content is success
    if (res.status === 204 || res.ok) {
      console.log('[API][Drivers] Session cancelled (v1):', sessionId);
      return { ok: true };
    }
    
    // Handle errors
    if (res.status === 404) {
      // Session not found - return success anyway (idempotent)
      console.log('[API][Drivers] Session not found (v1) - treating as cancelled:', sessionId);
      return { ok: true };
    }
    
    const errorText = await res.text().catch(() => 'Unknown error');
    throw new Error(`Cancel session failed (${res.status}): ${errorText}`);
  } catch (e) {
    console.warn('[API][Drivers] Cancel session (v1) failed:', e.message);
    // Return success anyway - idempotent operation
    return { ok: true };
  }
}

// ============================================
// Legacy Pilot Endpoints (DEPRECATED - will be removed)
// ============================================

if (typeof window !== 'undefined') {
  window.NeravaAPI = window.NeravaAPI || {};
  window.NeravaAPI.apiGet = apiGet;
  window.NeravaAPI.apiPost = apiPost;
  window.NeravaAPI.apiRegister = apiRegister;
  window.NeravaAPI.apiLogin = apiLogin;
  window.NeravaAPI.apiLogout = apiLogout;
  window.NeravaAPI.apiMe = apiMe;
  window.NeravaAPI.getCurrentUser = getCurrentUser;
  window.NeravaAPI.apiJoinChargeEvent = apiJoinChargeEvent;
  window.NeravaAPI.apiNearbyMerchants = apiNearbyMerchants;
  window.NeravaAPI.apiDriverWallet = apiDriverWallet;
  window.NeravaAPI.apiDriverActivity = apiDriverActivity;
  window.NeravaAPI.apiSessionPing = apiSessionPing;
  window.NeravaAPI.apiCancelSession = apiCancelSession;
  window.NeravaAPI.apiGetSmartcarConnectUrl = apiGetSmartcarConnectUrl;
  window.NeravaAPI.apiGetVehicleTelemetry = apiGetVehicleTelemetry;
  
  // Legacy pilot endpoints (deprecated)
  window.NeravaAPI.fetchPilotBootstrap = fetchPilotBootstrap;
  window.NeravaAPI.fetchPilotWhileYouCharge = fetchPilotWhileYouCharge;
  window.NeravaAPI.fetchMerchantOffer = fetchMerchantOffer;
}

const Api = {
  // Auth
  apiRegister,
  apiLogin,
  apiLogout,
  apiMe,
  getCurrentUser,
  
  // Drivers
  apiJoinChargeEvent,
  apiNearbyMerchants,
  apiDriverWallet,
  apiDriverActivity,
  apiSessionPing,
  apiCancelSession,
  
  // Utils
  apiGet,
  apiPost,
  
  // Constants
  EVENT_SLUG,
  ZONE_SLUG,
  
  // Legacy pilot endpoints (deprecated - remove after migration)
  fetchPilotBootstrap,
  fetchPilotWhileYouCharge,
  fetchMerchantOffer,
  pilotStartSession,
  pilotVerifyPing,
  pilotVerifyVisit,
  pilotCancelSession,
};

export default Api;