// Wallet page logic
import { apiGet, apiPost } from '../core/api.js';
window.Nerava = window.Nerava || {};
window.Nerava.pages = window.Nerava.pages || {};

function updateWalletProgress() {
  const progressEl = document.getElementById('walletProgress');
  if (progressEl) {
    const progress = progressEl.querySelector('.progress-bar');
    if (progress) {
      progress.style.width = '75%';
    }
  }
}

async function updateCommunityPool() {
  if (!window.Nerava.core.api.canCallApi()) return;
  
  try {
    const pool = await apiGet('/v1/social/pool');
    const poolEl = document.getElementById('communityPool');
    if (poolEl) {
      const amount = window.Nerava.core.utils.formatCurrency(pool.total_community_cents);
      poolEl.textContent = `Community shared this month: ${amount}`;
    }
  } catch (e) {
    console.error('Failed to load community pool:', e);
  }
}

async function loadPayoutHistory() {
  if (!window.Nerava.core.api.canCallApi()) return;
  
  try {
    const history = await apiGet('/v1/payouts/visa/history?user_id=current_user');
    const historyEl = document.getElementById('payoutHistory');
    if (historyEl && history.payouts) {
      historyEl.innerHTML = history.payouts.map(payout => `
        <div class="payout-item">
          <div class="payout-info">
            <div class="payout-amount">${window.Nerava.core.utils.formatCurrency(payout.amount_cents)}</div>
            <div class="payout-card">****${payout.card_number}</div>
          </div>
          <div class="payout-status ${payout.status}">${payout.status}</div>
          <div class="payout-date">${new Date(payout.created_at).toLocaleDateString()}</div>
        </div>
      `).join('');
    }
  } catch (e) {
    console.error('Failed to load payout history:', e);
  }
}

async function initiateWithdrawal() {
  if (!window.Nerava.core.api.canCallApi()) return;
  
  const amount = prompt('Enter withdrawal amount (in dollars):');
  if (!amount || isNaN(amount) || parseFloat(amount) <= 0) {
    alert('Please enter a valid amount');
    return;
  }
  
  const cardNumber = prompt('Enter card number (last 4 digits):');
  if (!cardNumber || cardNumber.length !== 4) {
    alert('Please enter the last 4 digits of your card');
    return;
  }
  
  try {
    const result = await apiPost('/v1/payouts/visa/direct', {
      method: 'POST',
      body: JSON.stringify({
        user_id: 'current_user',
        amount_cents: Math.round(parseFloat(amount) * 100),
        card_number: cardNumber
      })
    });
    
    if (result.success) {
      alert(`Withdrawal initiated! Transaction ID: ${result.transaction_id}`);
      loadPayoutHistory(); // Refresh history
    } else {
      alert(`Withdrawal failed: ${result.error || 'Unknown error'}`);
    }
  } catch (e) {
    console.error('Failed to initiate withdrawal:', e);
    alert('Withdrawal failed. Please try again.');
  }
}

async function loadRecentActivity() {
  if (!window.Nerava.core.api.canCallApi()) return;
  
  try {
    const exportData = await apiGet('/v1/demo/export');
    const activityEl = document.getElementById('wallet-activity');
    if (activityEl && exportData.events) {
      const recentEvents = exportData.events.slice(0, 5);
      activityEl.innerHTML = recentEvents.map(event => {
        const amount = window.Nerava.core.utils.formatCurrency(event.amount_cents || 0);
        const type = event.type === 'charge_verify' ? 'Verified charge' : 'Reward earned';
        const location = event.meta?.location || 'Station ABC';
        const kwh = event.meta?.kwh || '4.1';
        return `<li><span>${type} • ${location} • ${kwh} kWh</span><strong>+${amount}</strong></li>`;
      }).join('');
    }
  } catch (e) {
    console.error('Failed to load recent activity:', e);
  }
}

function initWallet() {
  updateWalletProgress();
  updateCommunityPool();
  loadPayoutHistory();
  loadRecentActivity();
  
  // Wire up withdraw button
  const withdrawBtn = document.getElementById('withdrawBtn');
  if (withdrawBtn) {
    withdrawBtn.addEventListener('click', initiateWithdrawal);
  }
}

// Export init function
window.Nerava.pages.wallet = {
  init: initWallet
};
