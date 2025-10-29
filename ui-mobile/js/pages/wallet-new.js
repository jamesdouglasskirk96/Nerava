export async function initWalletPage(rootEl) {
  console.log('WALLET-NEW.JS VERSION 3.0 - FRESH FILE');
  
  // Check if this is a payment success redirect
  const urlParams = new URLSearchParams(window.location.search);
  const paidParam = urlParams.get('paid');
  const isPaymentSuccess = paidParam !== null;
  
  rootEl.innerHTML = `
    <div style="padding: 20px; background: white; min-height: 400px;">
      ${isPaymentSuccess ? `
        <div style="background: #dcfce7; border: 1px solid #22c55e; color: #166534; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-weight: 600;">
          🎉 Payment completed! You earned rewards for this purchase.
        </div>
      ` : ''}
      <h1 style="color: #111827; font-size: 24px; margin-bottom: 20px;">Wallet</h1>
      <div style="background: #f8fafc; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <div style="font-size: 32px; font-weight: bold; color: #111827; margin-bottom: 8px;" id="w-balance">$3.98</div>
        <div style="color: #4b5563; font-size: 14px; margin-bottom: 8px;" id="w-kicker">7-day charging streak 🔥</div>
        <div style="background: #e2e8f0; color: #374151; padding: 4px 8px; border-radius: 6px; display: inline-block; font-size: 12px; font-weight: 600;" id="w-tier">Silver</div>
        <div style="margin-top: 16px; display: flex; gap: 12px;">
          <button style="background: #22c55e; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-weight: 600;" id="w-add">Add Funds</button>
          <button style="background: #f1f5f9; color: #0f172a; border: none; padding: 12px 20px; border-radius: 8px; font-weight: 600;" id="w-withdraw">Withdraw</button>
        </div>
      </div>
      
      <div style="background: #f8fafc; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <h2 style="color: #111827; font-size: 18px; margin-bottom: 16px;">Ways you earned</h2>
        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e2e8f0;">
          <span style="color: #374151;">Starbucks co-fund</span>
          <span style="color: #111827; font-weight: 600;">+$0.75</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e2e8f0;">
          <span style="color: #374151;">Off-peak award</span>
          <span style="color: #111827; font-weight: 600;">-$0.50</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 8px 0;">
          <span style="color: #374151;">Green Hour savings</span>
          <span style="color: #111827; font-weight: 600;">+$3.73</span>
        </div>
      </div>
    </div>
  `;

  // Load wallet data from API
  try {
    console.log('Wallet: About to call API...');
    const data = await window.NeravaAPI.apiGet('/v1/wallet/summary');
    console.log('Wallet: API response:', data);
    if (data) {
      
      // Update balance - show available credit instead of negative balance
      // API returns balance_cents or balanceCents
      const balanceCents = data.balance_cents || data.balanceCents || 0;
      const availableCredit = data.availableCreditCents || balanceCents;
      const balance = (availableCredit / 100).toFixed(2);
      const balanceEl = document.querySelector('#w-balance');
      if (balanceEl) {
        balanceEl.textContent = `$${balance}`;
        // Add subtitle if there's a negative net balance
        if (balanceCents < 0) {
          const subtitle = document.createElement('div');
          subtitle.style.cssText = 'font-size: 12px; color: #6b7280; margin-top: 4px;';
          subtitle.textContent = `Net: $${(balanceCents / 100).toFixed(2)} (after payments)`;
          balanceEl.parentNode.insertBefore(subtitle, balanceEl.nextSibling);
        }
      }
      
      // Update breakdown - find the earnings section and update it
      const breakdown = data.breakdown || [];
      const earningsList = rootEl.querySelector('#wallet-earnings');
      if (earningsList && breakdown.length > 0) {
        const listItems = breakdown.map(x => `
          <li class="list-item wallet-earn-row">
            <span class="label">${x.title}</span>
            <span class="value">${x.type === 'earn' ? '+' : '-'} $${(x.amountCents / 100).toFixed(2)}</span>
          </li>
        `).join('');
        earningsList.innerHTML = listItems;
      }

      // Update history - find the withdrawals section and update it
      const history = data.history || [];
      const historyList = rootEl.querySelector('#wallet-withdrawals');
      if (historyList && history.length > 0) {
        const listItems = history.map(x => `
          <li class="list-item wallet-earn-row">
            <span class="label">${x.title}</span>
            <span class="value">${x.type === 'earn' ? '+' : '-'} $${(x.amountCents / 100).toFixed(2)}</span>
          </li>
        `).join('');
        historyList.innerHTML = listItems;
      }
    } else {
      throw new Error('No data returned from API');
    }
  } catch (e) {
    console.error('Wallet API error:', e);
    // Keep the static demo data that's already in the HTML
  }

  // Wire demo actions
  document.querySelector('#w-add').addEventListener('click', () => alert('Add funds (coming soon)'));
  document.querySelector('#w-withdraw').addEventListener('click', () => alert('Withdraw (coming soon)'));
}
