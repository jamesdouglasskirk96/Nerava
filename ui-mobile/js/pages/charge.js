// Charge page logic
window.Nerava = window.Nerava || {};
window.Nerava.pages = window.Nerava.pages || {};

// Load charge feed from API
async function loadChargeFeed() {
  const listEl = document.querySelector('#chargeFeedList');
  if (!listEl) return;
  listEl.innerHTML = `<div class="muted">Loading activity…</div>`;
  try {
    const items = await window.Nerava.core.api.apiJson('/v1/social/feed');
    if (!items.length) {
      listEl.innerHTML = `<div class="muted">No recent activity yet.</div>`;
      return;
    }
    listEl.innerHTML = items.map(renderFeedRow).join('');
    wireFollowChips(listEl, items);
  } catch (e) {
    console.error(e);
    listEl.innerHTML = `<div class="muted">Unable to load activity right now.</div>`;
  }
}

function renderFeedRow(it) {
  const amt = (it.gross_cents / 100).toFixed(2);
  const when = window.Nerava.core.utils.formatTime(it.timestamp);
  const sub = [it.meta?.hub_name, it.meta?.city].filter(Boolean).join(' · ');
  const initials = (it.user_id || '??').slice(0,2).toUpperCase();

  return `
  <div class="feed-row" data-user="${it.user_id}">
    <div class="avatar">${initials}</div>
    <div class="feed-main">
      <div class="title"><b>${it.user_id}</b> earned $${amt}${it.meta?.kwh ? ` for ${it.meta.kwh} kWh` : ''}</div>
      <div class="sub">${sub || 'Nerava'}</div>
      <div class="meta muted">${when}</div>
    </div>
    <button class="chip follow-chip" data-user="${it.user_id}" aria-label="Follow ${it.user_id}">
      Follow
    </button>
  </div>`;
}

async function isFollowing(me, other) {
  if (!window.Nerava.core.api.canCallApi()) return false;
  const following = await window.Nerava.core.api.apiJson(`/v1/social/following?user_id=${encodeURIComponent(me)}`);
  return following.some(f => f.followee_id === other);
}

function wireFollowChips(scopeEl, items) {
  const me = window.NERAVA_USER_ID || 'you';
  scopeEl.querySelectorAll('.follow-chip').forEach(async btn => {
    const other = btn.dataset.user;
    if (other === me) { btn.remove(); return; }
    try {
      if (await isFollowing(me, other)) btn.classList.add('following'), btn.textContent = 'Following';
    } catch {}
    btn.addEventListener('click', async () => {
      const following = btn.classList.toggle('following');
      btn.textContent = following ? 'Following' : 'Follow';
      try {
        await window.Nerava.core.api.apiJson('/v1/social/follow', {
          method: 'POST',
          body: JSON.stringify({
            follower_id: me,
            followee_id: other,
            follow: following
          })
        });
      } catch (e) {
        btn.classList.toggle('following');
        btn.textContent = btn.classList.contains('following') ? 'Following' : 'Follow';
      }
    });
  });
}

function initCharge() {
  loadChargeFeed();
}

// Export init function
window.Nerava.pages.charge = {
  init: initCharge
};
