export async function initWalletPage(rootEl) {
  rootEl.innerHTML = `
    <div class="wallet-content stack">
      <!-- Balance / Actions -->
      <section class="card card--xl">
        <div class="row-between">
          <div class="col">
            <div class="kicker">Wallet</div>
            <div class="amount-lg" id="w-balance">$19.00</div>
            <div class="subtle" id="w-kicker">7-day charging streak 🔥</div>
          </div>
          <div class="pill" id="w-tier">Silver</div>
        </div>
        <div class="grid-2" style="margin-top:16px">
          <button class="btn btn-success btn-block" id="w-add">Add Funds</button>
          <button class="btn btn-ghost btn-block" id="w-withdraw">Withdraw</button>
        </div>
      </section>

      <!-- Earnings breakdown -->
      <section class="card card--pad">
        <div class="row-between">
          <div class="card-title">Ways you earned</div>
          <div class="badge good" id="w-boost">+14% community boost</div>
        </div>
        <ul class="list" id="w-breakdown">
          <!-- injected rows -->
        </ul>
      </section>

      <!-- Recent transactions -->
      <section class="card card--pad">
        <div class="row-between">
          <div class="card-title">Recent withdrawals</div>
          <div class="subtle" id="w-total">+$0.00</div>
        </div>
        <ul class="list" id="w-history"></ul>
      </section>
    </div>
  `;

  // --- Demo/fallback data (replace with API later) ---
  const breakdown = [
    { icon:'⚡', label:'Off-peak charging', amount:'+ $8.25' },
    { icon:'🏪', label:'Merchant perks',     amount:'+ $3.10' },
    { icon:'👥', label:'Community boost',    amount:'+ $2.65' },
  ];
  const history = [
    { who:'Green Hour', note:'You saved during Green Hour ☀️', amt:'+ $3.73' },
    { who:'Starbucks',  note:'Co-fund perk ☕️',                amt:'+ $0.75' },
    { who:'Off-peak',   note:'Award',                           amt:'+ $0.50' },
  ];

  document.querySelector('#w-breakdown').innerHTML = breakdown.map(x => `
    <li class="li">
      <div class="avatar">${x.icon}</div>
      <div class="col">
        <div>${x.label}</div>
      </div>
      <div class="badge">${x.amount}</div>
    </li>
  `).join('');

  document.querySelector('#w-history').innerHTML = history.map(x => `
    <li class="li">
      <div class="avatar">💸</div>
      <div class="col">
        <div><strong>${x.who}</strong></div>
        <div class="subtle">${x.note}</div>
      </div>
      <div class="badge">${x.amt}</div>
    </li>
  `).join('');

  // Wire demo actions
  document.querySelector('#w-add').addEventListener('click', () => alert('Add funds (coming soon)'));
  document.querySelector('#w-withdraw').addEventListener('click', () => alert('Withdraw (coming soon)'));
}