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

  try {
    const res = await fetch('/v1/activity', { credentials:'include' });
    const data = await res.json();

    // Reputation
    const { score, tier, streakDays } = data.reputation;
    const repTierEl = rootEl.querySelector('#rep-tier');
    const repScoreEl = rootEl.querySelector('#rep-score');
    const repNextEl  = rootEl.querySelector('#rep-next');
    const repFillEl  = rootEl.querySelector('#rep-fill');
    const repStreak  = rootEl.querySelector('#rep-streak');

    repTierEl.textContent = tier;
    repScoreEl.textContent = score;
    if (streakDays > 0) {
      repStreak.hidden = false;
      repStreak.textContent = `🔋 ${streakDays}-day streak`;
    }

            const ni = nextTierInfo(score);
            repFillEl.style.width = ni.pct + '%';
            repNextEl.textContent = ni.next
              ? `${ni.toNext} pts to ${ni.next.name}`
              : 'Top tier reached';

            // Add follower/following counts
            const repMeta = document.createElement('div');
            repMeta.className = 'rep-meta';
            repMeta.innerHTML = `
              <div class="rep-pill"><strong>${data.reputation.followers_count || 12}</strong> Followers</div>
              <div class="rep-pill"><strong>${data.reputation.following_count || 8}</strong> Following</div>
            `;
            rootEl.querySelector('.rep-stack').appendChild(repMeta);

    // Earnings
    const dollars = (data.totals.followCents/100).toFixed(2);
    rootEl.querySelector('#follow-total').textContent = `$${dollars}`;

    const ul = rootEl.querySelector('#follow-list');
    ul.innerHTML = data.followEarnings.map(item => {
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
  } catch (e) {
    console.error('activity error', e);
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