const BASE = localStorage.NERAVA_URL || location.origin;

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
  const res = await fetch(url.toString(), { credentials: 'include' });
  if (!res.ok) {
    throw new Error(`Pilot while-you-charge failed (${res.status})`);
  }
  return res.json();
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
  return res.json();
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
};

export default Api;