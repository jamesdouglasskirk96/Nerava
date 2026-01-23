// P1-1: Logger is imported dynamically in functions to avoid circular dependencies

// Determine API base URL based on environment
function getApiBase() {
  const origin = window.location.origin;
  const hostname = window.location.hostname;
  
  // PRIORITY 1: Local development - use same origin (no CORS)
  // This ensures http://localhost:8001/app calls http://localhost:8001/v1/... (same origin)
  // CRITICAL: On localhost, ALWAYS use local backend unless explicitly forced with ?force_prod=true
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.includes('192.168.') || hostname.includes('10.');
  const urlParams = new URLSearchParams(window.location.search);
  const forceProd = urlParams.get('force_prod') === 'true';
  
  if (isLocalhost && !forceProd) {
    // For localhost, check if we're on port 8080 (frontend) or 8001 (backend)
    // If on 8080, route API calls to 8001
    const port = window.location.port;
    if (port === '8080' || port === '') {
      // Frontend is on 8080 or default port, route to backend on 8001
      const backendUrl = `http://${hostname}:8001`;
      console.log('[API] Local dev detected - frontend on port', port, '- routing to backend:', backendUrl);
      return backendUrl;
    } else {
      // Backend is serving frontend (same origin)
      console.log('[API] Local dev detected - using same origin (no CORS):', origin);
      return '';
    }
  }
  
  // PRIORITY 2: Explicit production backend override (for testing prod from local)
  // Only use this if you explicitly want to test against production
  // Example: localStorage.setItem('NERAVA_PROD_BACKEND', 'https://web-production-526f6.up.railway.app')
  // OR add ?force_prod=true to URL
  const prodBackendOverride = localStorage.getItem('NERAVA_PROD_BACKEND');
  if ((forceProd || prodBackendOverride) && prodBackendOverride && prodBackendOverride.startsWith('http')) {
    console.log('[API] Using production backend (override URL):', prodBackendOverride);
    return prodBackendOverride;
  }
  
  // PRIORITY 3: Legacy localStorage override (only if not localhost)
  if (!isLocalhost && localStorage.NERAVA_URL) {
    console.log('[API] Using localStorage.NERAVA_URL override:', localStorage.NERAVA_URL);
    return localStorage.NERAVA_URL;
  }
  
  // PRIORITY 4: Vite environment variable (if using Vite)
  try {
    // eslint-disable-next-line no-undef
    if (import.meta && import.meta.env && import.meta.env.VITE_API_BASE_URL) {
      // eslint-disable-next-line no-undef
      console.log('[API] Using Vite env var:', import.meta.env.VITE_API_BASE_URL);
      return import.meta.env.VITE_API_BASE_URL;
    }
  } catch (e) {
    // import.meta not available
  }
  
  // PRIORITY 5: CloudFront domain - route to App Runner backend
  // CloudFront domains typically end with .cloudfront.net or custom domain
  const isCloudFront = hostname.includes('cloudfront.net') || 
                       hostname.includes('amazonaws.com') ||
                       (window.location.protocol === 'https:' && !isLocalhost);
  
  if (isCloudFront && !isLocalhost) {
    // Check for App Runner URL in config or environment
    // Priority: window.NERAVA_API_BASE > environment variable > default App Runner pattern
    if (window.NERAVA_API_BASE) {
      console.log('[API] Using App Runner backend from window.NERAVA_API_BASE:', window.NERAVA_API_BASE);
      return window.NERAVA_API_BASE;
    }
    
    // Try to detect App Runner URL from meta tag or config
    const apiBaseMeta = document.querySelector('meta[name="nerava-api-base"]');
    if (apiBaseMeta && apiBaseMeta.content) {
      console.log('[API] Using App Runner backend from meta tag:', apiBaseMeta.content);
      return apiBaseMeta.content;
    }
    
    // Default: if we're on CloudFront, we need to set the App Runner URL
    // This should be set via config.js or meta tag in production
    console.warn('[API] CloudFront detected but no App Runner URL configured. Using same origin (may cause CORS issues).');
    console.warn('[API] Set window.NERAVA_API_BASE or add <meta name="nerava-api-base" content="https://your-app-runner-url">');
  }
  
  // PRIORITY 6: Other production environments (Vercel, Railway, etc.)
  const protocol = window.location.protocol;
  const isVercel = hostname.includes('vercel.app');
  const isNeravaNetwork = hostname.includes('nerava.network');
  const isProduction = !isLocalhost && (protocol === 'https:' || isVercel || isNeravaNetwork);
  
  if (isProduction) {
    const prodUrl = 'https://web-production-526f6.up.railway.app';
    console.log('[API] Using production backend (Railway):', prodUrl);
    return prodUrl;
  }
  
  // Fallback: same origin
  console.log('[API] Using same origin (fallback):', origin);
  return '';
}

const BASE = getApiBase();

// Constants for Domain January charge party
export const EVENT_SLUG = 'domain_jan_2025';
export const ZONE_SLUG = 'domain_austin';

// Track if we're currently refreshing to avoid infinite loops
let isRefreshing = false;
let refreshPromise = null;

async function _req(path, opts = {}, retryOn401 = true) {
  // P0-7: Add request timeout (default 10 seconds)
  const timeoutMs = opts.timeoutMs || 10000;
  
  const headers = { 
    Accept: 'application/json',
    'Content-Type': 'application/json',
    ...opts.headers 
  };
  
  // Add Authorization header if access token exists
  const { getAccessToken } = await import('./auth.js');
  const accessToken = getAccessToken();
  // P1-1: Use logger instead of console.log (sanitizes sensitive data)
  const logger = await import('./logger.js');
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
    logger.log('[API] Request headers: Authorization header added (token present)');
  } else {
    logger.log('[API] Request headers: No auth token available');
  }
  
  const url = BASE + path;
  logger.log('[API] Making request to:', url, { method: opts.method || 'GET', headers });
  
  // Add cache control for GET requests to prevent stale data
  const fetchOpts = {
    headers,
    credentials: 'include',
    ...opts,
  };
  
  // For GET requests, add cache: 'no-store' to ensure fresh data
  if ((opts.method || 'GET').toUpperCase() === 'GET' && !opts.cache) {
    fetchOpts.cache = 'no-store';
  }
  
  // P0-7: Wrap fetch with AbortController for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  let r;
  try {
    r = await fetch(url, { ...fetchOpts, signal: controller.signal });
    clearTimeout(timeoutId);
  } catch (e) {
    clearTimeout(timeoutId);
    if (e.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeoutMs}ms: ${path}`);
    }
    throw e;
  }
  
  // P1-1: Use logger (already imported above)
  logger.log('[API] Response status:', r.status, r.statusText);
  
  // Capture X-Request-ID from response
  const requestId = r.headers.get('X-Request-ID');
  if (requestId) {
    logger.log(`[API] Request ID: ${requestId}`);
  }
  
  // Handle 404 gracefully - return null for missing resources
  if (r.status === 404) {
    // Only log warning if not silenced (e.g., for telemetry which is best-effort)
    if (!opts.silent404) {
      logger.warn(`[API] 404 for ${path} - resource not found`);
    }
    return null;
  }
  
  // Handle 401: try to refresh token and retry once
  if (r.status === 401 && retryOn401 && accessToken) {
    const errorText = await r.text().catch(() => 'Unknown error');
    const errorCode = r.headers.get('X-Error-Code');
    
    // If refresh_reuse_detected, clear tokens and redirect to login
    if (errorCode === 'refresh_reuse_detected') {
      const { clearTokens } = await import('./auth.js');
      clearTokens();
      window.location.hash = '#/login';
      throw new Error('Session expired. Please sign in again.');
    }
    
    // Try to refresh token
    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = (async () => {
        try {
          const { refreshAccessToken } = await import('./auth.js');
          const newToken = await refreshAccessToken();
          if (newToken) {
            return newToken;
          }
        } finally {
          isRefreshing = false;
          refreshPromise = null;
        }
        return null;
      })();
    }
    
    const newToken = await refreshPromise;
    
    if (newToken) {
      // Retry original request with new token (with timeout)
      headers['Authorization'] = `Bearer ${newToken}`;
      const retryController = new AbortController();
      const retryTimeoutId = setTimeout(() => retryController.abort(), timeoutMs);
      let retryResponse;
      try {
        retryResponse = await fetch(BASE + path, {
          headers,
          credentials: 'include',
          ...opts,
          signal: retryController.signal,
        });
        clearTimeout(retryTimeoutId);
      } catch (e) {
        clearTimeout(retryTimeoutId);
        if (e.name === 'AbortError') {
          throw new Error(`Request timeout after ${timeoutMs}ms: ${path}`);
        }
        throw e;
      }
      
      if (retryResponse.status === 404) {
        return null;
      }
      
      if (!retryResponse.ok) {
        const retryErrorText = await retryResponse.text().catch(() => 'Unknown error');
        throw new Error(`${retryResponse.status} ${path}: ${retryErrorText}`);
      }
      
      return retryResponse.json();
    } else {
      // Refresh failed - clear tokens and redirect to login
      const { clearTokens } = await import('./auth.js');
      clearTokens();
      window.location.hash = '#/login';
      throw new Error('Session expired. Please sign in again.');
    }
  }
  
  if (!r.ok) {
    const errorText = await r.text().catch(() => 'Unknown error');
    
    // Send telemetry event for API errors (best-effort, swallow errors)
    apiSendTelemetryEvent({
      event: 'API_ERROR',
      ts: Date.now(),
      page: window.location.hash || '/',
      meta: {
        path: path,
        status: r.status,
        error_preview: errorText.substring(0, 200) // No secrets
      }
    }).catch(() => {}); // Swallow errors
    
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

// Client telemetry event queue (throttled)
let _telemetryQueue = [];
let _telemetryFlushTimer = null;
let _telemetryEnabled = true;

export async function apiSendTelemetryEvent(eventData) {
  // Add to queue
  _telemetryQueue.push(eventData);
  
  // Throttle: flush at most once per 5 seconds
  if (!_telemetryFlushTimer) {
    _telemetryFlushTimer = setTimeout(async () => {
      await _flushTelemetryQueue();
      _telemetryFlushTimer = null;
    }, 5000);
  }
}

async function _flushTelemetryQueue() {
  if (_telemetryQueue.length === 0) return;
  if (!navigator.onLine) {
    _telemetryQueue = []; // Drop if offline
    return;
  }
  
  if (!_telemetryEnabled) {
    _telemetryQueue = []; // Disabled, clear queue
    return;
  }
  
  const batch = [..._telemetryQueue];
  _telemetryQueue = [];
  
  // Send each event (best-effort)
  for (const event of batch) {
    try {
      const result = await _req('/v1/telemetry/events', {
        method: 'POST',
        body: JSON.stringify(event),
        silent404: true, // Don't log 404 warnings for telemetry
      }, false); // Don't retry on 401

      // If null returned, endpoint doesn't exist - disable telemetry silently
      if (result === null) {
        _telemetryEnabled = false;
        return;
      }
    } catch (e) {
      // Swallow errors - telemetry is best-effort
    }
  }
}


/**
 * Get current user info
 */
export async function apiMe() {
  try {
    const user = await _req('/auth/me');
    
    // Store globally
    if (typeof window !== 'undefined') {
      window.NERAVA_USER = user;
      if (user.public_id) {
        localStorage.setItem('NERAVA_USER_PUBLIC_ID', user.public_id);
      }
    }
    
    return user;
  } catch (e) {
    // 401 means not logged in - that's OK
    if (e.message.includes('401') || e.message.includes('Unauthorized')) {
      if (typeof window !== 'undefined') {
        window.NERAVA_USER = null;
        localStorage.removeItem('NERAVA_USER_PUBLIC_ID');
      }
      return null;
    }
    console.error('[API][Auth] Failed to get current user:', e.message);
    throw e;
  }
}

/**
 * Google SSO login
 */
export async function apiGoogleLogin(idToken) {
  try {
    const response = await _req('/auth/google', {
      method: 'POST',
      body: JSON.stringify({ id_token: idToken }),
    });
    
    // Store tokens
    const { setTokens } = await import('./auth.js');
    setTokens(response.access_token, response.refresh_token);
    
    return response;
  } catch (e) {
    console.error('[API][Auth] Google login failed:', e.message);
    throw e;
  }
}

/**
 * Apple SSO login
 */
export async function apiAppleLogin(idToken) {
  try {
    const response = await _req('/auth/apple', {
      method: 'POST',
      body: JSON.stringify({ id_token: idToken }),
    });
    
    // Store tokens
    const { setTokens } = await import('./auth.js');
    setTokens(response.access_token, response.refresh_token);
    
    return response;
  } catch (e) {
    console.error('[API][Auth] Apple login failed:', e.message);
    throw e;
  }
}

/**
 * Start phone OTP flow
 */
export async function apiOtpStart(phone) {
  try {
    const response = await _req('/auth/otp/start', {
      method: 'POST',
      body: JSON.stringify({ phone }),
    });
    return response;
  } catch (e) {
    console.error('[API][Auth] OTP start failed:', e.message);
    throw e;
  }
}

/**
 * Verify phone OTP
 */
export async function apiOtpVerify(phone, code) {
  try {
    const response = await _req('/auth/otp/verify', {
      method: 'POST',
      body: JSON.stringify({ phone, code }),
    });
    
    // Store tokens
    const { setTokens } = await import('./auth.js');
    setTokens(response.access_token, response.refresh_token);
    
    return response;
  } catch (e) {
    console.error('[API][Auth] OTP verify failed:', e.message);
    throw e;
  }
}

/**
 * Dev mode login - auto-login as dev@nerava.local
 * Only works when DEMO_MODE is enabled on backend
 */
export async function apiDevLogin() {
  try {
    console.log('[API][Auth] Attempting dev login...');
    
    // Use fetch directly to get better error handling (don't return null for 404)
    const BASE = getApiBase();
    const url = BASE + '/auth/dev/login';
    console.log('[API][Auth] Dev login URL:', url);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    console.log('[API][Auth] Dev login response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error('[API][Auth] Dev login failed:', response.status, errorText);
      throw new Error(`Dev login failed: ${response.status} ${errorText}`);
    }
    
    const data = await response.json();
    console.log('[API][Auth] Dev login successful:', data);
    
    // Store tokens
    const { setTokens } = await import('./auth.js');
    setTokens(data.access_token, data.refresh_token);
    
    return data;
  } catch (e) {
    console.error('[API][Auth] Dev login failed:', e);
    console.error('[API][Auth] Error details:', {
      message: e.message,
      stack: e.stack
    });
    throw e;
  }
}

/**
 * Refresh access token
 */
export async function apiRefresh(refreshToken) {
  try {
    const response = await _req('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }, false); // Don't retry on 401 for refresh endpoint
    return response;
  } catch (e) {
    console.error('[API][Auth] Refresh failed:', e.message);
    throw e;
  }
}

/**
 * Logout
 */
export async function apiLogout(refreshToken = null) {
  try {
    const body = refreshToken ? { refresh_token: refreshToken } : {};
    await _req('/auth/logout', {
      method: 'POST',
      body: JSON.stringify(body),
    }, false); // Don't retry on 401 for logout
    
    // Clear local tokens
    const { clearTokens } = await import('./auth.js');
    clearTokens();
  } catch (e) {
    console.warn('[API][Auth] Logout failed:', e.message);
    // Clear tokens anyway
    const { clearTokens } = await import('./auth.js');
    clearTokens();
  }
}

// Export setTokens for use in login page
export async function setTokens(accessToken, refreshToken) {
  const { setTokens: _setTokens } = await import('./auth.js');
  _setTokens(accessToken, refreshToken);
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
export async function apiNearbyMerchants({ 
  lat, 
  lng, 
  zoneSlug, 
  radiusM = 5000,
  q = null,
  category = null,
  novaOnly = true,
  maxDistanceToChargerM = null
}) {
  console.log('[API] Calling nearby merchants:', { lat, lng, zoneSlug, radiusM, q, category, novaOnly, maxDistanceToChargerM });
  try {
    const params = new URLSearchParams({
      lat: String(lat),
      lng: String(lng),
      zone_slug: zoneSlug,
      radius_m: String(radiusM),
      nova_only: String(novaOnly),
    });
    
    if (q) {
      params.append('q', q);
    }
    if (category) {
      params.append('category', category);
    }
    if (maxDistanceToChargerM !== null) {
      params.append('max_distance_to_charger_m', String(maxDistanceToChargerM));
    }

    const url = `/v1/drivers/merchants/nearby?${params.toString()}`;
    console.log('[API] Request URL:', url);

    const res = await _req(url);
    console.log('[API] Response:', res);
    console.log('[API] Response type:', typeof res, Array.isArray(res));
    console.log('[API][Drivers] Nearby merchants:', res?.length || 0);
    return res || [];
  } catch (e) {
    console.error('[API] Nearby merchants error:', e);
    console.error('[API][Drivers] Failed to get nearby merchants:', e.message);
    return []; // Return empty array on error
  }
}

/**
 * Get nearby Nova-accepting merchants for Discover page
 */
export async function apiNovaMerchantsNearby({ lat, lng, radiusM = 2000 }) {
  try {
    const params = new URLSearchParams({
      radius_m: String(radiusM),
    });
    
    if (lat !== null && lat !== undefined) {
      params.append('lat', String(lat));
    }
    if (lng !== null && lng !== undefined) {
      params.append('lng', String(lng));
    }

    const url = `/v1/merchants/nova/nearby?${params.toString()}`;
    console.log('[API] Fetching Nova merchants:', url);

    const res = await _req(url);
    console.log('[API] Nova merchants response:', res?.length || 0, 'merchants');
    return res || [];
  } catch (e) {
    console.error('[API] Failed to get Nova merchants:', e.message);
    return []; // Return empty array on error
  }
}

/**
 * Get charger discovery data with nearby merchants
 */
export async function apiChargerDiscovery({ lat, lng, search = null }) {
  try {
    const params = new URLSearchParams({
      lat: String(lat),
      lng: String(lng),
    });
    
    if (search && search.trim()) {
      params.append('search', search.trim());
    }

    const url = `/v1/chargers/discovery?${params.toString()}`;
    console.log('[API] Fetching charger discovery:', url);

    const res = await _req(url);
    console.log('[API] Charger discovery response:', res?.chargers?.length || 0, 'chargers');
    return res || { chargers: [], within_radius: false, nearest_charger_id: null, nearest_distance_m: Infinity, radius_m: 400 };
  } catch (e) {
    console.error('[API] Failed to get charger discovery:', e.message);
    return { chargers: [], within_radius: false, nearest_charger_id: null, nearest_distance_m: Infinity, radius_m: 400 };
  }
}

/**
 * Track analytics event
 */
export async function trackEvent(event, meta = {}) {
  try {
    const BASE = getApiBase();
    const res = await fetch(`${BASE}/v1/telemetry/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        event,
        ts: Date.now(),
        page: window.location.pathname,
        meta
      })
    });
    
    if (!res.ok) {
      console.warn('[Analytics] Failed to track event:', event, res.status);
      return;
    }
    
    const data = await res.json();
    console.log('[Analytics] Tracked event:', event, data);
    return data;
  } catch (e) {
    // Silently fail analytics - don't break the app
    console.warn('[Analytics] Error tracking event:', event, e.message);
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
 * Get driver wallet summary (comprehensive wallet data for UI)
 */
export async function apiWalletSummary(forceRefresh = false) {
  try {
    // Add cache-busting timestamp if forceRefresh is true
    let path = '/v1/drivers/me/wallet/summary';
    if (forceRefresh) {
      const timestamp = Date.now();
      path += `?t=${timestamp}`;
    }
    const res = await _req(path);
    console.log('[API][Drivers] Wallet Summary:', res);
    return res;
  } catch (e) {
    console.error('[API][Drivers] Failed to get wallet summary:', e.message);
    throw e;
  }
}

/**
 * Redeem Nova from driver to merchant
 */
export async function apiRedeemNova(merchantId, amount, sessionId = null, idempotencyKey = null) {
  try {
    const body = {
      merchant_id: merchantId,
      amount: amount,
    };
    if (sessionId) body.session_id = sessionId;
    if (idempotencyKey) body.idempotency_key = idempotencyKey;

    const res = await _req('/v1/drivers/nova/redeem', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    console.log('[API][Nova] Redeem result:', res);
    return res;
  } catch (e) {
    console.error('[API][Nova] Failed to redeem Nova:', e.message);
    throw e;
  }
}

/**
 * Get driver activity/transactions
 * Returns empty array if endpoint doesn't exist (404) or on any error
 */
export async function apiDriverActivity({ limit = 50 } = {}) {
  try {
    const params = new URLSearchParams({ limit: String(limit) });
    const res = await _req(`/v1/drivers/activity?${params.toString()}`);
    
    // Handle 404 (endpoint doesn't exist) gracefully
    if (res === null) {
      console.warn('[API][Drivers] Activity endpoint not found (404) - returning empty list');
      return [];
    }
    
    console.log('[API][Drivers] Activity (v1):', res);
    
    // Backend returns array directly, or wrap if needed
    const events = Array.isArray(res) ? res : (res.events || res.transactions || []);
    return events || [];
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
// EV Status & Management
// ============================================

/**
 * Get vehicle connection status
 */
export async function apiEvStatus() {
  try {
    const res = await _req('/v1/ev/status');
    return res;
  } catch (e) {
    console.error('[API][EV] Failed to get EV status:', e.message);
    throw e;
  }
}

/**
 * Disconnect vehicle
 */
export async function apiEvDisconnect() {
  try {
    const res = await _req('/v1/ev/disconnect', {
      method: 'POST',
    });
    return res;
  } catch (e) {
    console.error('[API][EV] Failed to disconnect vehicle:', e.message);
    throw e;
  }
}

// ============================================
// Wallet Pass Management
// ============================================

/**
 * Get wallet pass status
 */
export async function apiWalletPassStatus() {
  try {
    const res = await _req('/v1/wallet/pass/status');
    return res;
  } catch (e) {
    console.error('[API][Wallet] Failed to get wallet pass status:', e.message);
    throw e;
  }
}

/**
 * Reinstall wallet pass (Apple or Google)
 */
export async function apiWalletPassReinstall(platform) {
  try {
    const res = await _req('/v1/wallet/pass/reinstall', {
      method: 'POST',
      body: JSON.stringify({ platform }),
    });
    return res;
  } catch (e) {
    console.error('[API][Wallet] Failed to reinstall wallet pass:', e.message);
    throw e;
  }
}

// ============================================
// Notification Preferences
// ============================================

/**
 * Get notification preferences
 */
export async function apiNotifPrefsGet() {
  try {
    const res = await _req('/v1/notifications/prefs');
    return res;
  } catch (e) {
    console.error('[API][Notifications] Failed to get preferences:', e.message);
    throw e;
  }
}

/**
 * Update notification preferences
 */
export async function apiNotifPrefsPut(prefs) {
  try {
    const res = await _req('/v1/notifications/prefs', {
      method: 'PUT',
      body: JSON.stringify(prefs),
    });
    return res;
  } catch (e) {
    console.error('[API][Notifications] Failed to update preferences:', e.message);
    throw e;
  }
}

// ============================================
// Account Management
// ============================================

/**
 * Request account data export
 */
export async function apiAccountExport() {
  try {
    const res = await _req('/v1/account/export', {
      method: 'POST',
    });
    return res;
  } catch (e) {
    console.error('[API][Account] Failed to request export:', e.message);
    throw e;
  }
}

/**
 * Delete account (requires confirmation)
 */
export async function apiAccountDelete() {
  try {
    const res = await _req('/v1/account', {
      method: 'DELETE',
      body: JSON.stringify({ confirmation: 'DELETE' }),
    });
    return res;
  } catch (e) {
    console.error('[API][Account] Failed to delete account:', e.message);
    throw e;
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
  window.NeravaAPI.apiNovaMerchantsNearby = apiNovaMerchantsNearby;
  window.NeravaAPI.trackEvent = trackEvent;
  window.NeravaAPI.apiDriverWallet = apiDriverWallet;
  window.NeravaAPI.apiWalletSummary = apiWalletSummary;
  window.NeravaAPI.apiDriverActivity = apiDriverActivity;
  window.NeravaAPI.apiSessionPing = apiSessionPing;
  window.NeravaAPI.apiCancelSession = apiCancelSession;
  window.NeravaAPI.apiRedeemNova = apiRedeemNova;
  window.NeravaAPI.apiGetSmartcarConnectUrl = apiGetSmartcarConnectUrl;
  window.NeravaAPI.apiGetVehicleTelemetry = apiGetVehicleTelemetry;
  window.NeravaAPI.apiEvStatus = apiEvStatus;
  window.NeravaAPI.apiEvDisconnect = apiEvDisconnect;
  window.NeravaAPI.apiWalletPassStatus = apiWalletPassStatus;
  window.NeravaAPI.apiWalletPassReinstall = apiWalletPassReinstall;
  window.NeravaAPI.apiNotifPrefsGet = apiNotifPrefsGet;
  window.NeravaAPI.apiNotifPrefsPut = apiNotifPrefsPut;
  window.NeravaAPI.apiAccountExport = apiAccountExport;
  window.NeravaAPI.apiAccountDelete = apiAccountDelete;
  
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
  apiNovaMerchantsNearby,
  trackEvent,
  apiDriverWallet,
  apiWalletSummary,
  apiDriverActivity,
  apiSessionPing,
  apiCancelSession,
  apiRedeemNova,
  
  // EV Management
  apiEvStatus,
  apiEvDisconnect,
  
  // Wallet Pass
  apiWalletPassStatus,
  apiWalletPassReinstall,
  
  // Notifications
  apiNotifPrefsGet,
  apiNotifPrefsPut,
  
  // Account Management
  apiAccountExport,
  apiAccountDelete,
  
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