import { loadDemoRedemption } from '../core/demo-state.js';

export async function initWalletPage(rootEl) {
  rootEl.innerHTML = `
    <div style="padding: 20px; background: white; min-height: 400px;">
      <h1 style="color: #111827; font-size: 24px; margin-bottom: 20px;">Wallet</h1>
      <div style="background: #f8fafc; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <div style="font-size: 32px; font-weight: bold; color: #111827; margin-bottom: 8px;" id="w-balance">$0.00</div>
        <div style="font-size: 16px; color: #64748b; margin-bottom: 8px;" id="w-nova-balance"></div>
        <div style="color: #4b5563; font-size: 14px; margin-bottom: 8px;" id="w-kicker">Start earning rewards!</div>
        <div style="background: #e2e8f0; color: #374151; padding: 4px 8px; border-radius: 6px; display: inline-block; font-size: 12px; font-weight: 600;" id="w-tier">Bronze</div>
        <div style="margin-top: 16px; display: flex; gap: 12px;">
          <button style="background: #22c55e; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-weight: 600;" id="w-add">Add Funds</button>
          <button style="background: #f1f5f9; color: #0f172a; border: none; padding: 12px 20px; border-radius: 8px; font-weight: 600;" id="w-withdraw">Withdraw</button>
        </div>
      </div>
    </div>
  `;

  // Load wallet data - start with demo state, then merge API response
  let walletData = {
    balance_dollars: '0.00',
    balance_cents: 0,
    nova_balance: 0
  };
  
  // Apply demo redemption state if available
  const demo = loadDemoRedemption();
  if (demo && typeof demo.wallet_nova_balance === 'number' && demo.wallet_nova_balance > 0) {
    walletData.nova_balance = demo.wallet_nova_balance;
    // Demo conversion: $0.10 per Nova
    walletData.balance_dollars = (demo.wallet_nova_balance * 0.10).toFixed(2);
    walletData.balance_cents = Math.round(demo.wallet_nova_balance * 10);
  }
  
  // Try to load from API (may fail in demo)
  try {
    const data = await window.NeravaAPI.apiGet('/v1/wallet/summary');
    if (data && data.balanceCents !== undefined) {
      // Merge API data, but keep demo nova balance if higher
      walletData.balance_dollars = (data.balanceCents / 100).toFixed(2);
      walletData.balance_cents = data.balanceCents;
      // If demo state has nova, prioritize that
      if (demo && demo.wallet_nova_balance > 0) {
        walletData.balance_dollars = (demo.wallet_nova_balance * 0.10).toFixed(2);
        walletData.balance_cents = Math.round(demo.wallet_nova_balance * 10);
      }
    }
  } catch (e) {
    // API failed - use demo state only
  }
  
  // Update balance display
  const balanceEl = document.querySelector('#w-balance');
  if (balanceEl) balanceEl.textContent = `$${walletData.balance_dollars}`;
  
  // Update Nova balance display
  const novaBalanceEl = document.querySelector('#w-nova-balance');
  if (novaBalanceEl && walletData.nova_balance > 0) {
    novaBalanceEl.textContent = `${walletData.nova_balance} Nova`;
    novaBalanceEl.style.display = 'block';
  } else if (novaBalanceEl) {
    novaBalanceEl.style.display = 'none';
  }
  
  // Update kicker text based on balance
  const kickerEl = document.querySelector('#w-kicker');
  if (kickerEl && walletData.nova_balance > 0) {
    kickerEl.textContent = `${demo?.streak_days || 1}-day charging streak 🔥`;
  }

  // Wire demo actions
  document.querySelector('#w-add').addEventListener('click', () => alert('Add funds (coming soon)'));
  document.querySelector('#w-withdraw').addEventListener('click', () => alert('Withdraw (coming soon)'));
}