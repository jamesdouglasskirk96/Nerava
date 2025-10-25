export async function initActivityPage(rootEl) {
  rootEl.innerHTML = `
  <section class="card card--pad rep-card">
    <div class="rep-head">Energy Reputation</div>
    <div class="rep-row">
      <div class="rep-icon" aria-hidden="true">
        <svg width="40" height="40" viewBox="0 0 48 48" fill="none">
          <!-- battery -->
          <rect x="4" y="12" width="36" height="24" rx="6" stroke="currentColor" stroke-width="2"></rect>
          <rect x="40" y="18" width="4" height="12" rx="2" fill="currentColor"></rect>
          <!-- bolt -->
          <path d="M26 14l-6 10h6l-2 10 8-12h-6l4-8z" fill="currentColor"></path>
        </svg>
      </div>
      <div class="rep-main">
        <div id="rep-tier" class="rep-tier badge">Bronze</div>
        <div class="rep-sub">Your impact & smart-charge consistency</div>
      </div>
      <div id="rep-score" class="rep-score">0</div>
    </div>
  </section>

  <section class="card card--pad">
    <div class="row space-between center">
      <div class="eyebrow">Follow earnings (last 30 days)</div>
      <div id="follow-total" class="amount">$0.00</div>
    </div>
    <ul id="follow-list" class="list list--people"></ul>
  </section>
  `;

  try {
    const r = await fetch('/v1/activity', { credentials:'include' });
    const data = await r.json();

    // Reputation
    rootEl.querySelector('#rep-tier').textContent = data.reputation.tier;
    rootEl.querySelector('#rep-score').textContent = data.reputation.score;

    // Total
    rootEl.querySelector('#follow-total').textContent = `$${(data.totalCents/100).toFixed(2)}`;

    // List
    const tierColor = (t)=>({
      Bronze: 'badge--bronze',
      Silver: 'badge--silver',
      Gold: 'badge--gold',
      Platinum: 'badge--platinum',
      'Grid Guardian': 'badge--guardian'
    }[t] || 'badge--bronze');

    const ul = rootEl.querySelector('#follow-list');
    ul.innerHTML = data.earnings.map(e => `
      <li class="list-item">
        <div class="avatar">${(e.handle||'M')[0].toUpperCase()}</div>
        <div class="col">
          <div class="title">@${e.handle}</div>
          <div class="sub">earned you</div>
        </div>
        <span class="badge ${tierColor(e.tier)}">${e.tier}</span>
        <div class="amount">$${(e.amountCents/100).toFixed(2)}</div>
      </li>
    `).join('');
  } catch (err) {
    console.error('activity page error', err);
    // Show fallback content
    rootEl.querySelector('#follow-list').innerHTML = '<li class="list-item">No earnings yet</li>';
  }
}
