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

if (typeof window !== 'undefined') {
  window.NeravaAPI = window.NeravaAPI || {};
  window.NeravaAPI.apiGet = apiGet;
  window.NeravaAPI.apiPost = apiPost;
  window.NeravaAPI.fetchPilotBootstrap = fetchPilotBootstrap;
  window.NeravaAPI.fetchPilotWhileYouCharge = fetchPilotWhileYouCharge;
}

const Api = {
  apiGet,
  apiPost,
  fetchPilotBootstrap,
  fetchPilotWhileYouCharge,
};

export default Api;