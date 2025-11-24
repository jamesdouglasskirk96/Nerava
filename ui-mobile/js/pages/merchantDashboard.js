/**
 * Merchant Dashboard Page
 * 
 * Shows merchant balance, recent redemptions, and code usage statistics.
 * Accessible via ?merchant={merchant_id} query param or direct navigation.
 */
import { apiGet } from '../core/api.js';
import { setTab } from '../app.js';

const $ = (s, r = document) => r.querySelector(s);

/**
 * Initialize the merchant dashboard
 * @param {Object} params - Parameters
 * @param {string} params.merchant_id - Merchant ID
 */
export async function initMerchantDashboard(params = {}) {
  // Extract merchant_id from hash route or query params
  let merchantId = params.merchant_id;
  
  if (!merchantId && location.hash) {
    const hashParams = new URLSearchParams(location.hash.split('?')[1] || '');
    merchantId = hashParams.get('merchant_id');
  }
  
  if (!merchantId) {
    const urlParams = new URLSearchParams(location.search);
    merchantId = urlParams.get('merchant');
  }
  
  const container = $('#page-merchant-dashboard');
  
  if (!container) {
    console.error('Merchant dashboard container not found');
    return;
  }

  if (!merchantId) {
    container.innerHTML = `
      <div class="page-content" style="padding: 20px; text-align: center;">
        <div style="color: #ef4444; margin-bottom: 20px;">
          Merchant ID required
        </div>
        <button class="btn btn-secondary" onclick="history.back()">
          Go Back
        </button>
      </div>
    `;
    return;
  }

  // Show loading state
  container.innerHTML = `
    <div class="page-content" style="padding: 20px; text-align: center;">
      <div style="font-size: 16px; color: #64748b;">Loading dashboard...</div>
    </div>
  `;

  try {
    // Fetch balance and report in parallel
    const [balanceData, reportData] = await Promise.all([
      fetchBalance(merchantId).catch(e => {
        console.warn('Failed to fetch balance:', e);
        return null;
      }),
      fetchReport(merchantId).catch(e => {
        console.warn('Failed to fetch report:', e);
        return null;
      })
    ]);

    // Fetch merchant name if available
    let merchantName = 'Merchant';
    try {
      const bootstrap = await window.NeravaAPI.fetchPilotBootstrap();
      const whileYouCharge = await window.NeravaAPI.fetchPilotWhileYouCharge();
      const merchants = whileYouCharge.recommended_merchants || [];
      const merchant = merchants.find(m => m.id === merchantId);
      if (merchant) merchantName = merchant.name;
    } catch (e) {
      console.warn('Could not fetch merchant name:', e);
    }

    renderDashboard(merchantId, merchantName, balanceData, reportData);
  } catch (error) {
    console.error('Failed to load merchant dashboard:', error);
    container.innerHTML = `
      <div class="page-content" style="padding: 20px;">
        <div style="text-align: center; color: #ef4444; margin-bottom: 20px;">
          Failed to load dashboard
        </div>
        <button class="btn btn-primary" style="width: 100%;" onclick="location.reload()">
          Try Again
        </button>
      </div>
    `;
  }
}

/**
 * Fetch merchant balance
 */
async function fetchBalance(merchantId) {
  return await apiGet(`/v1/merchants/${merchantId}/balance`);
}

/**
 * Fetch merchant report (for redemptions)
 */
async function fetchReport(merchantId) {
  return await apiGet(`/v1/merchants/${merchantId}/report`, { period: 'week' });
}

/**
 * Render the dashboard UI
 */
function renderDashboard(merchantId, merchantName, balanceData, reportData) {
  const container = $('#page-merchant-dashboard');
  if (!container) return;

  const balanceCents = balanceData?.balance_cents || 0;
  const balanceDollars = (balanceCents / 100).toFixed(2);
  
  // Extract redemption data from report (if available)
  // Note: We'll need to fetch redemption events separately or from report
  const evVisits = reportData?.ev_visits || 0;
  const totalRewards = reportData?.total_rewards_cents || 0;

  container.innerHTML = `
    <div class="page-content" style="padding: 20px; max-width: 800px; margin: 0 auto;">
      <!-- Header -->
      <div style="margin-bottom: 24px;">
        <h1 style="font-size: 28px; font-weight: 700; color: #111827; margin-bottom: 8px;">
          ${merchantName} Dashboard
        </h1>
        <p style="font-size: 14px; color: #64748b;">
          Merchant ID: ${merchantId}
        </p>
      </div>

      <!-- Balance Card -->
      <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
      ">
        <div style="color: rgba(255,255,255,0.9); font-size: 14px; margin-bottom: 8px;">
          Available Balance
        </div>
        <div style="font-size: 48px; font-weight: 700; color: white; margin-bottom: 16px;">
          $${balanceDollars}
        </div>
        <button 
          id="btn-replenish"
          class="btn"
          style="
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
          "
        >
          Replenish Nova Balance
        </button>
      </div>

      <!-- Stats Grid -->
      <div style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      ">
        <div style="background: #f8fafc; padding: 20px; border-radius: 12px; text-align: center;">
          <div style="font-size: 32px; font-weight: 700; color: #111827; margin-bottom: 4px;">
            ${evVisits}
          </div>
          <div style="font-size: 14px; color: #64748b;">
            EV Visits
          </div>
        </div>
        <div style="background: #f8fafc; padding: 20px; border-radius: 12px; text-align: center;">
          <div style="font-size: 32px; font-weight: 700; color: #111827; margin-bottom: 4px;">
            $${(totalRewards / 100).toFixed(2)}
          </div>
          <div style="font-size: 14px; color: #64748b;">
            Total Rewards
          </div>
        </div>
      </div>

      <!-- Recent Redemptions -->
      <div style="background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <h2 style="font-size: 18px; font-weight: 600; color: #111827; margin-bottom: 16px;">
          Recent Redemptions
        </h2>
        <div id="redemptions-table" style="overflow-x: auto;">
          <table style="width: 100%; border-collapse: collapse;">
            <thead>
              <tr style="border-bottom: 1px solid #e2e8f0;">
                <th style="text-align: left; padding: 12px; font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase;">
                  Code
                </th>
                <th style="text-align: left; padding: 12px; font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase;">
                  Amount
                </th>
                <th style="text-align: left; padding: 12px; font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase;">
                  Date
                </th>
              </tr>
            </thead>
            <tbody id="redemptions-tbody">
              <tr>
                <td colspan="3" style="padding: 20px; text-align: center; color: #94a3b8;">
                  Loading redemptions...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Actions -->
      <div style="display: flex; gap: 12px;">
        <button 
          id="btn-back"
          class="btn btn-secondary"
          style="flex: 1; padding: 14px; font-size: 16px;"
        >
          ← Back
        </button>
      </div>
    </div>
  `;

  // Wire up buttons
  $('#btn-replenish')?.addEventListener('click', () => {
    alert('Replenish balance feature coming soon');
  });
  
  $('#btn-back')?.addEventListener('click', () => {
    if (window.setTab) {
      window.setTab('explore');
    } else {
      history.back();
    }
  });

  // Load redemptions (for now, show placeholder - would need redemption history endpoint)
  loadRedemptions(merchantId);
}

/**
 * Load redemption history
 * Note: This would need a new endpoint or we can derive from report data
 */
async function loadRedemptions(merchantId) {
  const tbody = $('#redemptions-tbody');
  if (!tbody) return;

  try {
    // For now, show placeholder message
    // In production, would fetch from /v1/merchants/{id}/redemptions or similar
    tbody.innerHTML = `
      <tr>
        <td colspan="3" style="padding: 20px; text-align: center; color: #94a3b8;">
          No redemptions yet this week
        </td>
      </tr>
    `;
  } catch (error) {
    console.error('Failed to load redemptions:', error);
    tbody.innerHTML = `
      <tr>
        <td colspan="3" style="padding: 20px; text-align: center; color: #ef4444;">
          Failed to load redemptions
        </td>
      </tr>
    `;
  }
}

// Export for global access
if (typeof window !== 'undefined') {
  window.initMerchantDashboard = initMerchantDashboard;
}

