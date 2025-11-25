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
  
  // Production: use Railway backend
  if (isProduction) {
    const prodUrl = 'https://web-production-526f6.up.railway.app';
    console.log('[API] Using production backend:', prodUrl);
    return prodUrl;
  }
  
  // Development: use localhost
  const devUrl = 'http://127.0.0.1:8001';
  console.log('[API] Using development backend:', devUrl);
  return devUrl;
}

const BASE = getApiBase();

async function _req(path, opts = {}) {
  const r = await fetch(BASE + path, {
    headers: { Accept: 'application/json' },
    credentials: 'include',
    ...opts,
  });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

export const apiGet = (path, params) => {
  const url = new URL(BASE + path);
  Object.entries(params || {}).forEach(([k, v]) => url.searchParams.set(k, v));
  return _req(url.pathname + url.search);
};

export async function apiPost(path, body = {}, headers = {}) {
  return _req(path, { method: 'POST', body, headers });
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

if (typeof window !== 'undefined') {
  window.NeravaAPI = window.NeravaAPI || {};
  window.NeravaAPI.apiGet = apiGet;
  window.NeravaAPI.apiPost = apiPost;
  window.NeravaAPI.fetchPilotBootstrap = fetchPilotBootstrap;
  window.NeravaAPI.fetchPilotWhileYouCharge = fetchPilotWhileYouCharge;
  window.NeravaAPI.fetchMerchantOffer = fetchMerchantOffer;
}

const Api = {
  apiGet,
  apiPost,
  fetchPilotBootstrap,
  fetchPilotWhileYouCharge,
  fetchMerchantOffer,
  pilotStartSession,
  pilotVerifyPing,
  pilotVerifyVisit,
  pilotCancelSession,
};

export default Api;