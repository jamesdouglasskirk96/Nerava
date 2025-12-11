import { getChargingState, getOptimalChargingTime, getChargingStateDisplay } from '../core/charging-state.js';
import { apiDriverWallet, apiDriverActivity } from '../core/api.js';
import { loadDemoRedemption } from '../core/demo-state.js';
import { setTab } from '../app.js';

// Tier thresholds for reputation
const TIERS = [
  { name: 'Bronze', min: 0, color: '#9CA3AF' },
  { name: 'Silver', min: 100, color: '#64748B' },
  { name: 'Gold', min: 300, color: '#EAB308' },
  { name: 'Platinum', min: 700, color: '#06B6D4' },
];

function getTierInfo(score) {
  const sorted = [...TIERS].sort((a, b) => a.min - b.min);
  let current = sorted[0];
  let next = null;
  for (let i = 0; i < sorted.length; i++) {
    if (score >= sorted[i].min) current = sorted[i];
    if (score < sorted[i].min) {
      next = sorted[i];
      break;
    }
  }
  const toNext = next ? next.min - score : 0;
  const pct = next
    ? Math.max(0, Math.min(100, ((score - current.min) / (next.min - current.min)) * 100))
    : 100;
  return { current, next, toNext, pct };
}

export async function initWalletPage(rootEl) {
  console.log('[Wallet] Initializing wallet page...');

  // Get charging state for hero
  const chargingState = getChargingState();
  const optimalTime = getOptimalChargingTime();
  const stateDisplay = getChargingStateDisplay();

  // Check if this is a payment success redirect
  const urlParams = new URLSearchParams(window.location.search);
  const paidParam = urlParams.get('paid');
  const isPaymentSuccess = paidParam !== null;

  rootEl.innerHTML = `
    <div style="padding: 20px; background: white; min-height: calc(100vh - 140px);">
      ${isPaymentSuccess ? `
        <div style="background: #dcfce7; border: 1px solid #22c55e; color: #166534; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-weight: 600;">
          🎉 Payment completed! You earned rewards for this purchase.
        </div>
      ` : ''}
      
      <!-- Charging State Hero -->
      <div id="wallet-charging-hero" style="background: linear-gradient(135deg, ${stateDisplay.color}15 0%, ${stateDisplay.color}05 100%); border: 1px solid ${stateDisplay.color}30; border-radius: 16px; padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
          <span style="font-size: 24px;">${stateDisplay.icon}</span>
          <div style="flex: 1;">
            <div style="font-size: 18px; font-weight: 700; color: #111827; margin-bottom: 4px;">
              ${stateDisplay.label} Charging
            </div>
            <div style="font-size: 14px; color: #4b5563;">
              ${optimalTime.message}
            </div>
          </div>
        </div>
      </div>
      
      <!-- Nova Balance Card -->
      <div style="background: #f8fafc; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <div style="font-size: 14px; color: #64748b; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">Nova Balance</div>
        <div style="font-size: 36px; font-weight: bold; color: #111827; margin-bottom: 4px;" id="w-balance">$0.00</div>
        <div style="font-size: 14px; color: #64748b; margin-bottom: 16px;" id="w-nova-balance">0 Nova</div>
        
        <!-- Quick Actions -->
        <div style="display: flex; gap: 8px; margin-bottom: 16px;">
          <button id="w-scan-btn" style="flex: 1; background: #3b82f6; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: 600; font-size: 14px;">
            Scan QR
          </button>
          <button id="w-show-qr" style="flex: 1; background: #f1f5f9; color: #0f172a; border: none; padding: 12px; border-radius: 8px; font-weight: 600; font-size: 14px;">
            Show QR
          </button>
        </div>
        
        <!-- Reputation Progress -->
        <div id="wallet-reputation" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e2e8f0;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 13px; font-weight: 600; color: #374151;">Energy Reputation</span>
            <span id="w-tier-badge" style="background: #e2e8f0; color: #374151; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 600;">Bronze</span>
          </div>
          <div style="background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 4px;">
            <div id="w-tier-progress" style="background: ${TIERS[0].color}; height: 100%; width: 0%; transition: width 0.3s;"></div>
          </div>
          <div id="w-tier-next" style="font-size: 11px; color: #6b7280;">Loading...</div>
        </div>
      </div>
      
      <!-- Condensed Activity Feed -->
      <div style="background: white; border-radius: 12px; padding: 16px; margin-bottom: 20px; border: 1px solid #e2e8f0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin: 0;">Recent Activity</h3>
          <button id="w-view-all-activity" style="background: none; border: none; color: #3b82f6; font-size: 13px; font-weight: 600; cursor: pointer; padding: 4px 8px;">
            View all
          </button>
        </div>
        <ul id="wallet-activity-list" style="list-style: none; padding: 0; margin: 0;">
          <li style="padding: 12px 0; color: #9ca3af; font-size: 14px; text-align: center;">Loading activity...</li>
        </ul>
      </div>
    </div>
  `;

  // Load wallet data
  let walletData = {
    balance_dollars: '10.00',
    balance_cents: 1000,
    nova_balance: 1000,
    reputation_score: 0,
  };

  // Apply demo redemption state if available
  const demo = loadDemoRedemption();
  if (demo) {
    if (typeof demo.wallet_nova_balance === 'number' && demo.wallet_nova_balance > 0) {
      walletData.nova_balance = demo.wallet_nova_balance;
      walletData.balance_dollars = (demo.wallet_nova_balance * 0.10).toFixed(2);
      walletData.balance_cents = Math.round(demo.wallet_nova_balance * 10);
    }
    if (demo.reputation_score) {
      walletData.reputation_score = demo.reputation_score;
    }
  }

  // Try to load from v1 API
  try {
    const wallet = await apiDriverWallet();
    console.log('[Wallet] Wallet (v1) data:', wallet);

    if (wallet) {
      if (typeof wallet.nova_balance === 'number') {
        walletData.nova_balance = wallet.nova_balance;
        walletData.balance_dollars = (wallet.nova_balance * 0.10).toFixed(2);
        walletData.balance_cents = Math.round(wallet.nova_balance * 10);
      }

      // Merge with demo state if demo has higher balance
      if (demo && demo.wallet_nova_balance > walletData.nova_balance) {
        walletData.nova_balance = demo.wallet_nova_balance;
        walletData.balance_dollars = (demo.wallet_nova_balance * 0.10).toFixed(2);
        walletData.balance_cents = Math.round(demo.wallet_nova_balance * 10);
      }

      if (wallet.reputation_score) {
        walletData.reputation_score = wallet.reputation_score;
      }
    }
  } catch (e) {
    console.warn('[Wallet] Failed to load wallet from API:', e.message);
  }

  // Update balance display
  const balanceEl = rootEl.querySelector('#w-balance');
  const novaBalanceEl = rootEl.querySelector('#w-nova-balance');
  if (balanceEl) balanceEl.textContent = `$${walletData.balance_dollars}`;
  if (novaBalanceEl) novaBalanceEl.textContent = `${Math.round(walletData.nova_balance).toLocaleString()} Nova`;

  // Update reputation display
  const repScore = walletData.reputation_score || 0;
  const tierInfo = getTierInfo(repScore);
  const tierBadgeEl = rootEl.querySelector('#w-tier-badge');
  const tierProgressEl = rootEl.querySelector('#w-tier-progress');
  const tierNextEl = rootEl.querySelector('#w-tier-next');

  if (tierBadgeEl) {
    tierBadgeEl.textContent = tierInfo.current.name;
    tierBadgeEl.style.background = `${tierInfo.current.color}20`;
    tierBadgeEl.style.color = tierInfo.current.color;
  }

  if (tierProgressEl) {
    tierProgressEl.style.width = `${tierInfo.pct}%`;
    tierProgressEl.style.background = tierInfo.current.color;
  }

  if (tierNextEl) {
    if (tierInfo.next) {
      tierNextEl.textContent = `${tierInfo.toNext} pts to ${tierInfo.next.name}`;
    } else {
      tierNextEl.textContent = 'Top tier reached! 🎉';
    }
  }

  // Load activity feed (last 5 items)
  try {
    const activities = await apiDriverActivity({ limit: 5 });
    console.log('[Wallet] Activity data:', activities);

    const activityListEl = rootEl.querySelector('#wallet-activity-list');
    if (activityListEl && activities && activities.length > 0) {
      activityListEl.innerHTML = activities.slice(0, 5).map((item) => {
        const when = item.created_at
          ? new Date(item.created_at).toLocaleDateString(undefined, {
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
            })
          : 'Recently';
        const novaAmount = item.nova_amount || item.amount || 0;
        const description =
          item.description ||
          item.metadata?.reason ||
          `${item.type || 'Activity'}: ${novaAmount} Nova`;

        return `
          <li style="padding: 12px 0; border-bottom: 1px solid #f3f4f6; display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
              <div style="font-size: 14px; color: #111827; margin-bottom: 4px;">${description}</div>
              <div style="font-size: 12px; color: #6b7280;">${when}</div>
            </div>
            ${novaAmount > 0 ? `<div style="font-size: 14px; font-weight: 600; color: #22c55e;">+${novaAmount} Nova</div>` : ''}
          </li>
        `;
      }).join('');

      if (activities.length === 0) {
        activityListEl.innerHTML =
          '<li style="padding: 12px 0; color: #9ca3af; font-size: 14px; text-align: center;">No activity yet</li>';
      }
    }
  } catch (e) {
    console.warn('[Wallet] Failed to load activity:', e.message);
    const activityListEl = rootEl.querySelector('#wallet-activity-list');
    if (activityListEl) {
      activityListEl.innerHTML =
        '<li style="padding: 12px 0; color: #9ca3af; font-size: 14px; text-align: center;">Unable to load activity</li>';
    }
  }

  // Wire actions
  function handleShowWalletQr() {
    console.log('[Wallet] Show QR tapped');
    // Navigate to existing QR code page if it exists
    window.location.hash = '#/code';
  }

  rootEl.querySelector('#w-show-qr')?.addEventListener('click', handleShowWalletQr);

  rootEl.querySelector('#w-scan-btn')?.addEventListener('click', () => {
    console.log('[Wallet] Scan QR clicked - navigating to Discovery');
    setTab('discover');
    // TODO: Could open QR scanner directly from here if needed
  });

  rootEl.querySelector('#w-view-all-activity')?.addEventListener('click', () => {
    // Open activity page as modal or navigate
    console.log('[Wallet] View all activity clicked');
    // For now, could show a modal or navigate to full activity view
    // This can be enhanced later to show activity.js content in a modal
  });
}
