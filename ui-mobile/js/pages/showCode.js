/**
 * Show Code Page - Display discount code to merchant
 * 
 * Shows a redemption code for the driver to display to the merchant cashier.
 * Includes code, discount amount, merchant name, and expiration info.
 */
import { apiGet, apiPost } from '../core/api.js';
import { setTab } from '../app.js';

const $ = (s, r = document) => r.querySelector(s);

let currentOffer = null;
let expirationCheckInterval = null;

/**
 * Initialize the show code page
 * @param {Object} params - URL parameters or state
 * @param {string} params.merchant_id - Merchant ID
 * @param {string} params.code - Optional pre-loaded code (from state)
 * @param {number} params.amount_cents - Optional pre-loaded amount
 */
export async function initShowCode(params = {}) {
  // Extract merchant_id from hash route if not in params
  let merchantId = params.merchant_id;
  if (!merchantId && location.hash) {
    const hashParams = new URLSearchParams(location.hash.split('?')[1] || '');
    merchantId = hashParams.get('merchant_id');
  }
  
  // Get merchant name from sessionStorage if available
  if (!params.merchant_name && merchantId && typeof sessionStorage !== 'undefined') {
    params.merchant_name = sessionStorage.getItem(`merchant_name_${merchantId}`);
  }
  
  const container = $('#page-show-code');
  
  if (!container) {
    console.error('Show code page container not found');
    return;
  }

  // Show loading state
  container.innerHTML = `
    <div class="page-content" style="padding: 20px; text-align: center;">
      <div style="font-size: 16px; color: #64748b;">Loading discount code...</div>
    </div>
  `;

  try {
    // If code is already in params/state, use it; otherwise fetch new one
    if (params.code && params.amount_cents) {
      currentOffer = {
        code: params.code,
        amount_cents: params.amount_cents,
        merchant_id: merchantId,
        expires_at: params.expires_at
      };
      renderCode();
    } else {
      // Fetch merchant name first
      const merchantName = await fetchMerchantName(merchantId);
      
      // Generate new offer code
      await generateAndShowCode(merchantId, merchantName);
    }

    // Start expiration check interval
    startExpirationCheck();
  } catch (error) {
    console.error('Failed to load discount code:', error);
    container.innerHTML = `
      <div class="page-content" style="padding: 20px;">
        <div style="text-align: center; color: #ef4444; margin-bottom: 20px;">
          Failed to load discount code
        </div>
        <button 
          class="btn btn-primary" 
          style="width: 100%;"
          onclick="location.reload()"
        >
          Try Again
        </button>
        <button 
          class="btn btn-secondary" 
          style="width: 100%; margin-top: 12px;"
          onclick="window.setTab && window.setTab('explore')"
        >
          Back to Explore
        </button>
      </div>
    `;
  }
}

/**
 * Fetch merchant name from API or use cached data
 */
async function fetchMerchantName(merchantId) {
  try {
    // Try to get from pilot bootstrap or while-you-charge
    const bootstrap = await window.NeravaAPI.fetchPilotBootstrap();
    const whileYouCharge = await window.NeravaAPI.fetchPilotWhileYouCharge();
    
    // Look for merchant in merchants list
    const merchants = whileYouCharge.recommended_merchants || [];
    const merchant = merchants.find(m => m.id === merchantId);
    
    return merchant ? merchant.name : 'Merchant';
  } catch (e) {
    console.warn('Could not fetch merchant name:', e);
    return 'Merchant';
  }
}

/**
 * Generate a new offer code and display it
 */
async function generateAndShowCode(merchantId, merchantName) {
  try {
    const { fetchMerchantOffer } = await import('../core/api.js');
    const response = await fetchMerchantOffer(merchantId, 500);  // Default $5 discount

    if (!response || !response.code) {
      throw new Error('Invalid response from server');
    }

    currentOffer = {
      code: response.code,
      amount_cents: response.amount_cents,
      merchant_id: merchantId,
      merchant_name: merchantName,
      expires_at: response.expires_at
    };

    // Store in sessionStorage for offline access
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.setItem(`offer_${merchantId}`, JSON.stringify(currentOffer));
    }

    renderCode();
  } catch (error) {
    console.error('Failed to generate offer code:', error);
    throw error;
  }
}

/**
 * Render the discount code UI
 */
function renderCode() {
  const container = $('#page-show-code');
  if (!container || !currentOffer) return;

  const amountDollars = (currentOffer.amount_cents / 100).toFixed(2);
  const merchantName = currentOffer.merchant_name || 'Merchant';
  const expiresAt = currentOffer.expires_at ? new Date(currentOffer.expires_at) : null;
  
  container.innerHTML = `
    <div class="page-content" style="padding: 24px; max-width: 500px; margin: 0 auto;">
      <!-- Header -->
      <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="font-size: 24px; font-weight: 700; color: #111827; margin-bottom: 8px;">
          Discount Code
        </h1>
        <p style="font-size: 16px; color: #64748b;">
          Show this to the cashier at ${merchantName}
        </p>
      </div>

      <!-- Code Display Card -->
      <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 32px;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        margin-bottom: 24px;
      ">
        <div style="
          font-size: 48px;
          font-weight: 700;
          color: white;
          letter-spacing: 4px;
          font-family: 'Courier New', monospace;
          margin-bottom: 16px;
          text-shadow: 0 2px 8px rgba(0,0,0,0.2);
        " id="discount-code">${currentOffer.code}</div>
        
        <div style="
          font-size: 20px;
          font-weight: 600;
          color: rgba(255,255,255,0.9);
          margin-bottom: 8px;
        ">
          Save $${amountDollars}
        </div>
        
        ${expiresAt ? `
          <div style="
            font-size: 14px;
            color: rgba(255,255,255,0.8);
          " id="expiration-info">
            Valid until ${expiresAt.toLocaleDateString()} ${expiresAt.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
          </div>
        ` : ''}
      </div>

      <!-- Instructions -->
      <div style="
        background: #f8fafc;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
      ">
        <div style="
          font-size: 16px;
          font-weight: 600;
          color: #111827;
          margin-bottom: 12px;
        ">
          💡 How to use:
        </div>
        <ol style="
          margin: 0;
          padding-left: 20px;
          color: #475569;
          font-size: 14px;
          line-height: 1.6;
        ">
          <li style="margin-bottom: 8px;">Present this code to the cashier</li>
          <li style="margin-bottom: 8px;">Cashier will enter the code at checkout</li>
          <li style="margin-bottom: 8px;">The discount will be applied automatically</li>
        </ol>
      </div>

      <!-- Actions -->
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <button 
          id="btn-copy-code"
          class="btn btn-primary"
          style="width: 100%; padding: 14px; font-size: 16px; font-weight: 600;"
        >
          📋 Copy Code
        </button>
        <button 
          id="btn-back"
          class="btn btn-secondary"
          style="width: 100%; padding: 14px; font-size: 16px;"
        >
          ← Back to Explore
        </button>
      </div>
    </div>
  `;

  // Wire up buttons
  $('#btn-copy-code')?.addEventListener('click', copyCodeToClipboard);
  $('#btn-back')?.addEventListener('click', () => {
    if (window.setTab) {
      window.setTab('explore');
    } else {
      history.back();
    }
  });
}

/**
 * Copy code to clipboard
 */
async function copyCodeToClipboard() {
  if (!currentOffer) return;

  try {
    await navigator.clipboard.writeText(currentOffer.code);
    
    // Show success feedback
    const btn = $('#btn-copy-code');
    if (btn) {
      const originalText = btn.textContent;
      btn.textContent = '✓ Copied!';
      btn.style.background = '#22c55e';
      
      setTimeout(() => {
        btn.textContent = originalText;
        btn.style.background = '';
      }, 2000);
    }
  } catch (error) {
    console.error('Failed to copy code:', error);
    alert('Failed to copy code. Please manually select and copy.');
  }
}

/**
 * Check if code has expired and refresh if needed
 */
function startExpirationCheck() {
  // Clear any existing interval
  if (expirationCheckInterval) {
    clearInterval(expirationCheckInterval);
  }

  // Check every 60 seconds
  expirationCheckInterval = setInterval(() => {
    if (!currentOffer || !currentOffer.expires_at) return;

    const expiresAt = new Date(currentOffer.expires_at);
    const now = new Date();

    if (now >= expiresAt) {
      // Code expired, try to refresh
      const merchantId = currentOffer.merchant_id;
      const merchantName = currentOffer.merchant_name;
      
      // Show expiration message
      const container = $('#page-show-code');
      if (container) {
        container.innerHTML = `
          <div class="page-content" style="padding: 20px; text-align: center;">
            <div style="color: #ef4444; margin-bottom: 20px;">
              ⏰ This code has expired
            </div>
            <button 
              class="btn btn-primary" 
              style="width: 100%;"
              id="btn-refresh-code"
            >
              Get New Code
            </button>
          </div>
        `;
        
        $('#btn-refresh-code')?.addEventListener('click', async () => {
          try {
            await generateAndShowCode(merchantId, merchantName);
          } catch (error) {
            alert('Failed to generate new code. Please try again.');
          }
        });
      }

      clearInterval(expirationCheckInterval);
    }
  }, 60000); // Check every minute
}

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    if (expirationCheckInterval) {
      clearInterval(expirationCheckInterval);
    }
  });
}

// Export for global access
if (typeof window !== 'undefined') {
  window.initShowCode = initShowCode;
}

