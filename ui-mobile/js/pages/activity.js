// Simple tier thresholds (adjust later)
const TIERS = [
  { name: 'Bronze',  min: 0,   color: '#9CA3AF' },
  { name: 'Silver',  min: 100, color: '#64748B' },
  { name: 'Gold',    min: 300, color: '#EAB308' },
  { name: 'Platinum',min: 700, color: '#06B6D4' },
];

function nextTierInfo(score) {
  const sorted = [...TIERS].sort((a,b)=>a.min-b.min);
  let current = sorted[0], next = null;
  for (let i=0;i<sorted.length;i++){
    if (score >= sorted[i].min) current = sorted[i];
    if (score < sorted[i].min){ next = sorted[i]; break; }
  }
  return { current, next, toNext: next ? (next.min - score) : 0, pct: next ? Math.max(0, Math.min(100, (score - current.min) / (next.min - current.min) * 100)) : 100 };
}

import { loadDemoRedemption } from '../core/demo-state.js';

export async function initActivityPage(rootEl) {
  rootEl.innerHTML = `
    <section class="card card--pad rep-card--centered">
      <div class="rep-head">Energy Reputation</div>

      <div class="rep-stack">
        <!-- Vertical Battery with bolt -->
        <div class="rep-icon--vertical" aria-label="Energy battery">
          <!-- Outline battery SVG (vertical) -->
          <svg viewBox="0 0 72 128" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <rect x="10" y="8" width="52" height="108" rx="10" stroke="currentColor" stroke-width="4"/>
            <rect x="28" y="0" width="16" height="8" rx="3" fill="currentColor"/>
            <!-- bolt -->
            <path d="M40 54h-9l8-18H32l-7 22h9l-8 24h7l7-28z" fill="#3B82F6" opacity=".9"/>
          </svg>
        </div>

        <div class="rep-tier" id="rep-tier">Bronze</div>
        <div class="rep-score" id="rep-score">0</div>
        <div class="chip chip--streak" id="rep-streak" hidden>🔋 0-day streak</div>

        <!-- Progress to next tier -->
        <div class="rep-progress">
          <div class="rep-progress__bar"><div class="rep-progress__fill" id="rep-fill" style="width:0%"></div></div>
          <div class="rep-progress__label" id="rep-next">—</div>
        </div>

        <div class="rep-sub">Your impact & smart-charge consistency</div>
      </div>
    </section>

    <section class="card card--pad">
      <div class="row space-between center">
        <div class="eyebrow">FOLLOW EARNINGS (LAST 30 DAYS)</div>
        <div id="follow-total" class="amount">$0.00</div>
      </div>
      <ul id="follow-list" class="list list--people"></ul>
    </section>
  `;

  // Get DOM references for reputation display
  const repTierEl = rootEl.querySelector('#rep-tier');
  const repScoreEl = rootEl.querySelector('#rep-score');
  const repNextEl  = rootEl.querySelector('#rep-next');
  const repFillEl  = rootEl.querySelector('#rep-fill');
  const repStreak  = rootEl.querySelector('#rep-streak');

  // Load demo state first (to apply even if API fails)
  const demo = loadDemoRedemption();

  // Apply demo redemption state for reputation
  if (demo) {
    const demoScore = demo.reputation_score || 10;
    const demoStreak = demo.streak_days || 1;
    const demoTier = demoScore >= 100 ? 'Gold' : demoScore >= 50 ? 'Silver' : 'Bronze';
    
    if (repScoreEl) repScoreEl.textContent = String(demoScore);
    if (repStreak) {
      repStreak.hidden = false;
      repStreak.textContent = `🔋 ${demoStreak}-day streak`;
    }
    if (repTierEl) repTierEl.textContent = demoTier;
    
    // Update progress bar
    const ni = nextTierInfo(demoScore);
    if (repFillEl) repFillEl.style.width = ni.pct + '%';
    if (repNextEl) {
      repNextEl.textContent = ni.next
        ? `${ni.toNext} pts to ${ni.next.name}`
        : 'Top tier reached';
    }
  }

  try {
    // Use pilot activity endpoint instead of legacy endpoint
    const userId = localStorage.NERAVA_USER_ID || '123';  // TODO: Get actual user_id
    let data;
    try {
      data = await window.NeravaAPI.apiGet('/v1/pilot/activity', { user_id: userId, limit: 50 });
    } catch (apiError) {
      // Handle API errors gracefully - still show demo state
      console.warn(`[Activity] Failed to load activity: ${apiError.message || 'Unknown error'}`);
      data = null; // Will fall through to demo-only rendering
    }
    
    // If we have API data, merge it with demo state for reputation
    if (data && data.reputation) {
      const reputation = data.reputation;
      const apiScore = reputation.score || 0;
      const apiTier = reputation.tier || 'Bronze';
      const apiStreakDays = reputation.streakDays || 0;
      
      // Use demo state if it's higher/more recent, otherwise use API
      const finalScore = (demo && demo.reputation_score) ? Math.max(demo.reputation_score, apiScore) : apiScore;
      const finalTier = (demo && demo.reputation_score >= 50) ? (demo.reputation_score >= 100 ? 'Gold' : 'Silver') : apiTier;
      const finalStreak = (demo && demo.streak_days) ? Math.max(demo.streak_days, apiStreakDays) : apiStreakDays;
      
      if (repTierEl) repTierEl.textContent = finalTier;
      if (repScoreEl) repScoreEl.textContent = String(finalScore);
      if (finalStreak > 0 && repStreak) {
        repStreak.hidden = false;
        repStreak.textContent = `🔋 ${finalStreak}-day streak`;
      }
      
      const ni = nextTierInfo(finalScore);
      if (repFillEl) repFillEl.style.width = ni.pct + '%';
      if (repNextEl) {
        repNextEl.textContent = ni.next
          ? `${ni.toNext} pts to ${ni.next.name}`
          : 'Top tier reached';
      }

      // Add follower/following counts from API
      const repMeta = document.createElement('div');
      repMeta.className = 'rep-meta';
      repMeta.innerHTML = `
        <div class="rep-pill"><strong>${reputation.followers_count || 12}</strong> Followers</div>
        <div class="rep-pill"><strong>${reputation.following_count || 8}</strong> Following</div>
      `;
      rootEl.querySelector('.rep-stack').appendChild(repMeta);
    } else if (!demo) {
      // No API data and no demo - show defaults
      if (repTierEl) repTierEl.textContent = 'Bronze';
      if (repScoreEl) repScoreEl.textContent = '0';
      if (repStreak) repStreak.hidden = true;
      if (repFillEl) repFillEl.style.width = '0%';
      if (repNextEl) repNextEl.textContent = '—';
    }

    // Earnings - use demo state if available
    let followTotal = data?.totals?.followCents || 0;
    if (demo && demo.nova_awarded) {
      // Convert demo Nova to dollars ($0.10 per Nova for demo)
      const demoDollars = (demo.nova_awarded * 0.10);
      followTotal = Math.max(followTotal, Math.round(demoDollars * 100));
    }
    const dollars = (followTotal/100).toFixed(2);
    rootEl.querySelector('#follow-total').textContent = `$${dollars}`;

    // Render pilot activities (sessions, rewards, merchant visits)
    const ul = rootEl.querySelector('#follow-list');
    let hasActivities = false;
    
    if (data && data.activities && data.activities.length > 0) {
      ul.innerHTML = data.activities.map(item => {
        hasActivities = true;
        // Format activity based on type
        if (item.type === 'session') {
          const merchantName = item.merchant_name || 'No merchant selected';
          const chargerName = item.charger_name || 'Unknown Charger';
          const status = item.status === 'verified' ? 'Completed' : 'In Progress';
          return `
            <li class="intent">
              <div class="intent__main">
                <div class="title">Charged at ${chargerName}</div>
                <div class="sub">${merchantName !== 'No merchant selected' ? `Visited ${merchantName}` : 'No merchant visit'}</div>
                <div class="sub" style="font-size: 11px; color: #666; margin-top: 4px;">Status: ${status}</div>
              </div>
            </li>
          `;
        } else if (item.type === 'reward') {
          const merchantName = item.merchant_name ? `, visited ${item.merchant_name}` : '';
          const novaAmount = item.nova_awarded || 0;
          return `
            <li class="intent">
              <div class="intent__main">
                <div class="title">Earned ${novaAmount} Nova${merchantName}</div>
                <div class="sub">${item.source === 'merchant_visit' ? 'Merchant Visit Reward' : 'Charging Reward'}</div>
                <div class="sub" style="font-size: 11px; color: #666; margin-top: 4px;">${item.ts ? new Date(item.ts).toLocaleString() : ''}</div>
              </div>
            </li>
          `;
        } else if (item.type === 'wallet') {
          const merchantName = item.meta?.merchant_id ? ` from merchant visit` : '';
          const novaDelta = item.nova_delta || 0;
          const sign = novaDelta >= 0 ? '+' : '';
          return `
            <li class="intent">
              <div class="intent__main">
                <div class="title">${sign}${novaDelta} Nova${merchantName}</div>
                <div class="sub">${item.reason || 'Wallet Update'}</div>
                <div class="sub" style="font-size: 11px; color: #666; margin-top: 4px;">${item.ts ? new Date(item.ts).toLocaleString() : ''}</div>
              </div>
            </li>
          `;
        }
        return '';
      }).filter(Boolean).join('');
    }
    
    // Add demo redemption activity if available
    if (demo && demo.redeemed_at) {
      hasActivities = true;
      const when = new Date(demo.redeemed_at);
      const whenLabel = when.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
      const merchantName = demo.merchant_name || 'Merchant';
      const novaAmount = demo.nova_awarded || 0;
      
      // Prepend demo redemption to activity list
      const demoRow = `
        <li class="intent">
          <div class="intent__main">
            <div class="title">Redeemed at ${merchantName}</div>
            <div class="sub">${whenLabel} • In-store redemption</div>
            <div class="sub" style="font-size: 11px; color: #666; margin-top: 4px;">+${novaAmount} Nova</div>
          </div>
        </li>
      `;
      
      if (ul.innerHTML) {
        ul.innerHTML = demoRow + ul.innerHTML;
      } else {
        ul.innerHTML = demoRow;
      }
    }
    
    // Show empty state only if no activities at all
    if (!hasActivities) {
      ul.innerHTML = '<li class="intent"><div class="sub">No activity yet</div></li>';
    }

    // Legacy followEarnings rendering (fallback if needed)
    if (data.followEarnings && data.followEarnings.length > 0) {
      ul.innerHTML += data.followEarnings.map(item => {
        const earned = (item.amountCents/100).toFixed(2);
        const ctx = item.context ? item.context : 'charged nearby';
        return `
          <li class="list-item list-item--tight">
            <div class="avatar">${(item.handle||'m')[0].toUpperCase()}</div>
            <div class="col">
              <div class="title dark">@${item.handle}</div>
              <div class="sub dark-70">${ctx}</div>
              <div class="sub dark-90">You earned <b>$${earned}</b></div>
            </div>
            <span class="badge badge--tier badge--${(item.tier||'Bronze').toLowerCase()}">${item.tier||'Bronze'}</span>
          </li>
        `;
      }).join('');
    }
  } catch (e) {
    // Log concise error without stack trace
    console.warn(`[Activity] Error loading activity: ${e.message || 'Unknown error'}`);
    // Show fallback content with demo data
    rootEl.querySelector('#rep-tier').textContent = 'Silver';
    rootEl.querySelector('#rep-score').textContent = '180';
    rootEl.querySelector('#follow-total').textContent = '$2.75';
    rootEl.querySelector('#rep-streak').hidden = false;
    rootEl.querySelector('#rep-streak').textContent = '🔋 7-day streak';
    
    const ni = nextTierInfo(180);
    rootEl.querySelector('#rep-fill').style.width = ni.pct + '%';
    rootEl.querySelector('#rep-next').textContent = ni.next
      ? `${ni.toNext} pts to ${ni.next.name}`
      : 'Top tier reached';
    
    // Add follower/following counts for demo
    const repMeta = document.createElement('div');
    repMeta.className = 'rep-meta';
    repMeta.innerHTML = `
      <div class="rep-pill"><strong>12</strong> Followers</div>
      <div class="rep-pill"><strong>8</strong> Following</div>
    `;
    rootEl.querySelector('.rep-stack').appendChild(repMeta);
    
    rootEl.querySelector('#follow-list').innerHTML = `
      <li class="list-item list-item--tight">
        <div class="avatar">A</div>
        <div class="col">
          <div class="title dark">@alex</div>
          <div class="sub dark-70">charged and chilled at Starbucks</div>
          <div class="sub dark-90">You earned <b>$1.85</b></div>
        </div>
        <span class="badge badge--tier badge--gold">Gold</span>
      </li>
      <li class="list-item list-item--tight">
        <div class="avatar">S</div>
        <div class="col">
          <div class="title dark">@sam</div>
          <div class="sub dark-70">topped up at Target</div>
          <div class="sub dark-90">You earned <b>$0.90</b></div>
        </div>
        <span class="badge badge--tier badge--bronze">Bronze</span>
      </li>
      <li class="list-item list-item--tight">
        <div class="avatar">R</div>
        <div class="col">
          <div class="title dark">@riley</div>
          <div class="sub dark-70">smart-charged at Whole Foods</div>
          <div class="sub dark-90">You earned <b>$0.75</b></div>
        </div>
        <span class="badge badge--tier badge--silver">Silver</span>
      </li>
      <li class="list-item list-item--tight">
        <div class="avatar">J</div>
        <div class="col">
          <div class="title dark">@jordan</div>
          <div class="sub dark-70">queued and earned at H-E-B</div>
          <div class="sub dark-90">You earned <b>$1.20</b></div>
        </div>
        <span class="badge badge--tier badge--gold">Gold</span>
      </li>
      <li class="list-item list-item--tight">
        <div class="avatar">M</div>
        <div class="col">
          <div class="title dark">@morgan</div>
          <div class="sub dark-70">plugged in at Costco</div>
          <div class="sub dark-90">You earned <b>$0.60</b></div>
        </div>
        <span class="badge badge--tier badge--bronze">Bronze</span>
      </li>
    `;
  }
}