// Charge page logic
import { apiGet, apiPost } from '../core/api.js';

// Load charge feed from API
async function loadChargeFeed() {
  const listEl = document.querySelector('#chargeFeedList');
  if (!listEl) return;
  listEl.innerHTML = `<div class="muted">Loading activity…</div>`;
  try {
    const items = await apiGet('/v1/social/feed');
    if (!items.length) {
      listEl.innerHTML = `<div class="muted">No recent activity yet.</div>`;
      return;
    }
    listEl.innerHTML = items.map(renderFeedRow).join('');
    wireFollowChips(listEl, items);
  } catch (e) {
    console.error(e);
    listEl.innerHTML = `<div class="muted">Unable to load activity.</div>`;
  }
}

function renderFeedRow(item) {
  const timeAgo = formatTimeAgo(new Date(item.timestamp));
  return `
    <div class="feed-row">
      <div class="feed-avatar">
        <img src="/app/img/avatar-demo.svg" alt="User" />
      </div>
      <div class="feed-content">
        <div class="feed-header">
          <span class="feed-user">${item.user_name || 'User'}</span>
          <span class="feed-time">${timeAgo}</span>
        </div>
        <div class="feed-text">${item.description || 'Charged at ' + (item.location || 'hub')}</div>
        <div class="feed-actions">
          <button class="follow-chip" data-user-id="${item.user_id}">
            ${item.is_following ? 'Following' : 'Follow'}
          </button>
        </div>
      </div>
    </div>
  `;
}

function wireFollowChips(container, items) {
  container.querySelectorAll('.follow-chip').forEach(btn => {
    btn.onclick = async () => {
      const userId = btn.dataset.userId;
      const isFollowing = btn.textContent === 'Following';
      
      try {
        await apiPost('/v1/social/follow', { user_id: userId, follow: !isFollowing });
        btn.textContent = isFollowing ? 'Follow' : 'Following';
        btn.classList.toggle('following', !isFollowing);
      } catch (e) {
        console.error('Follow toggle failed:', e);
      }
    };
  });
}

function formatTimeAgo(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffMins < 1) return 'now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

// Initialize charge page with verify-by-location fallback
export function initChargePage(){
  const root = document.getElementById('page-charge');
  if(!root) return;
  const cardId = 'verify-card';
  let card = document.getElementById(cardId);
  if(!card){
    card = document.createElement('div');
    card.id = cardId; card.className = 'verify-card';
    card.innerHTML = `
      <h3>Verify by location</h3>
      <p>Stand near the charger and tap verify. We'll confirm eligibility automatically.</p>
      <button id="btn-verify-loc" class="verify-btn">Verify now</button>
    `;
    root.prepend(card);
  }
  const btn = document.getElementById('btn-verify-loc');
  if(btn){
    btn.onclick = async ()=>{
      if(!navigator.geolocation){ alert('Location is required.'); return; }
      navigator.geolocation.getCurrentPosition(async pos=>{
        try{
          // Optional: ping backend you already wired; this is best-effort.
          await apiPost('/v1/dual/tick', {
            session_id: window.dualSession?.id || 0,
            user_pos: { lat: pos.coords.latitude, lng: pos.coords.longitude },
            charger_pos: window.dualSession?.charger
              ? { lat: window.dualSession.charger.lat, lng: window.dualSession.charger.lng }
              : { lat: 30.4025, lng: -97.7258 },
            merchant_pos: window.dualSession?.merchant
              ? { lat: window.dualSession.merchant.lat, lng: window.dualSession.merchant.lng }
              : { lat: 30.4032, lng: -97.7241 },
          }).catch(()=>{});
          toast('Checking… move near the merchant to complete verification.');
        }catch{ toast('Verification queued.'); }
      }, ()=>alert('Please enable location services.'));
    };
  }
}

function toast(msg){
  const t = document.createElement('div');
  t.style.cssText='position:fixed;left:50%;bottom:calc(var(--tabbar-height) + 18px);transform:translateX(-50%);background:#111;color:#fff;padding:10px 14px;border-radius:12px;z-index:9999;font-weight:700';
  t.textContent = msg; document.body.appendChild(t); setTimeout(()=>t.remove(), 2600);
}

// Load feed when page becomes active
document.addEventListener('DOMContentLoaded', () => {
  loadChargeFeed();
});