import { apiGet, apiPost } from '../core/api.js';

export async function initVirtualCardPage(rootEl) {
  console.log('[VirtualCard] Initializing virtual card page...');

  rootEl.innerHTML = `
    <div style="padding: 20px; background: white; min-height: calc(100vh - 140px);">
      <div style="margin-bottom: 24px;">
        <h1 style="font-size: 24px; font-weight: 700; color: #111827; margin-bottom: 8px;">Virtual Card</h1>
        <p style="font-size: 14px; color: #6b7280;">Use Nova like a card</p>
      </div>

      <!-- Card Display Area -->
      <div id="vc-card-display" style="display: none; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); border-radius: 16px; padding: 24px; margin-bottom: 24px; color: white;">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 32px;">
          <div>
            <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">NOVA</div>
            <div style="font-size: 18px; font-weight: 600;">Virtual Card</div>
          </div>
          <div id="vc-brand" style="font-size: 24px; font-weight: 700;">VISA</div>
        </div>
        <div style="font-size: 24px; font-weight: 600; letter-spacing: 2px; margin-bottom: 16px;" id="vc-card-number">
          •••• •••• •••• <span id="vc-last4"></span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: end;">
          <div>
            <div style="font-size: 11px; opacity: 0.9; margin-bottom: 4px;">EXPIRES</div>
            <div style="font-size: 14px; font-weight: 600;" id="vc-expiry">--/--</div>
          </div>
          <div id="vc-status-badge" style="background: rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600;">
            Active
          </div>
        </div>
      </div>

      <!-- No Card State -->
      <div id="vc-no-card" style="text-align: center; padding: 40px 20px;">
        <div style="font-size: 48px; margin-bottom: 16px;">💳</div>
        <h2 style="font-size: 20px; font-weight: 600; color: #111827; margin-bottom: 8px;">No Virtual Card Yet</h2>
        <p style="font-size: 14px; color: #6b7280; margin-bottom: 24px;">
          Generate a virtual card to use your Nova balance anywhere cards are accepted.
        </p>
        <button id="vc-generate-btn" style="background: #3b82f6; color: white; border: none; padding: 14px 28px; border-radius: 8px; font-weight: 600; font-size: 16px; cursor: pointer; width: 100%; max-width: 300px;">
          Generate Virtual Card
        </button>
      </div>

      <!-- Coming Soon Modal (hidden by default) -->
      <div id="vc-coming-soon-modal" style="display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
        <div style="background: white; border-radius: 16px; padding: 24px; max-width: 320px; margin: 20px;">
          <h3 style="font-size: 20px; font-weight: 600; color: #111827; margin-bottom: 12px;">Coming Soon</h3>
          <p style="font-size: 14px; color: #6b7280; margin-bottom: 24px;">
            Virtual card generation is not yet available. We're working on bringing you this feature soon!
          </p>
          <button id="vc-modal-close" style="background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; font-size: 14px; cursor: pointer; width: 100%;">
            Got it
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div id="vc-loading" style="display: none; text-align: center; padding: 40px 20px;">
        <div style="font-size: 24px; margin-bottom: 16px;">⏳</div>
        <p style="font-size: 14px; color: #6b7280;">Generating your virtual card...</p>
      </div>

      <!-- Error State -->
      <div id="vc-error" style="display: none; background: #fee2e2; border: 1px solid #fecaca; color: #991b1b; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 14px;">
        <div id="vc-error-message"></div>
      </div>
    </div>
  `;

  // Load existing card
  await loadVirtualCard(rootEl);

  // Wire generate button
  rootEl.querySelector('#vc-generate-btn')?.addEventListener('click', async () => {
    await generateVirtualCard(rootEl);
  });

  // Wire modal close
  rootEl.querySelector('#vc-modal-close')?.addEventListener('click', () => {
    const modal = rootEl.querySelector('#vc-coming-soon-modal');
    if (modal) modal.style.display = 'none';
  });
}

async function loadVirtualCard(rootEl) {
  try {
    const card = await apiGet('/v1/virtual_cards/me');
    
    if (card && card.card_id) {
      // Show card display
      rootEl.querySelector('#vc-no-card').style.display = 'none';
      rootEl.querySelector('#vc-card-display').style.display = 'block';
      
      // Update card details
      const last4El = rootEl.querySelector('#vc-last4');
      const expiryEl = rootEl.querySelector('#vc-expiry');
      const brandEl = rootEl.querySelector('#vc-brand');
      const statusEl = rootEl.querySelector('#vc-status-badge');
      
      if (last4El) last4El.textContent = card.last4 || '0000';
      if (expiryEl) {
        const month = String(card.exp_month || 12).padStart(2, '0');
        const year = String(card.exp_year || 2028).slice(-2);
        expiryEl.textContent = `${month}/${year}`;
      }
      if (brandEl) brandEl.textContent = card.brand || 'VISA';
      if (statusEl) {
        statusEl.textContent = card.status === 'active' ? 'Active' : card.status || 'Active';
        if (card.status !== 'active') {
          statusEl.style.background = 'rgba(255,255,255,0.15)';
        }
      }
    } else {
      // No card - show generate button
      rootEl.querySelector('#vc-no-card').style.display = 'block';
      rootEl.querySelector('#vc-card-display').style.display = 'none';
    }
  } catch (e) {
    console.warn('[VirtualCard] Failed to load card:', e.message);
    // If 404 or feature disabled, show no card state
    rootEl.querySelector('#vc-no-card').style.display = 'block';
    rootEl.querySelector('#vc-card-display').style.display = 'none';
  }
}

async function generateVirtualCard(rootEl) {
  const noCardEl = rootEl.querySelector('#vc-no-card');
  const loadingEl = rootEl.querySelector('#vc-loading');
  const errorEl = rootEl.querySelector('#vc-error');
  const errorMsgEl = rootEl.querySelector('#vc-error-message');
  
  // Hide error, show loading
  if (errorEl) errorEl.style.display = 'none';
  if (noCardEl) noCardEl.style.display = 'none';
  if (loadingEl) loadingEl.style.display = 'block';

  try {
    const card = await apiPost('/v1/virtual_cards/create', {});
    
    // Success - reload card display
    if (loadingEl) loadingEl.style.display = 'none';
    await loadVirtualCard(rootEl);
    
  } catch (e) {
    console.error('[VirtualCard] Failed to generate card:', e);
    
    if (loadingEl) loadingEl.style.display = 'none';
    
    // Check if feature is disabled (501) or VIRTUAL_CARD_DISABLED error
    if (e.message && (e.message.includes('501') || e.message.includes('VIRTUAL_CARD_DISABLED'))) {
      // Show coming soon modal
      const modal = rootEl.querySelector('#vc-coming-soon-modal');
      if (modal) modal.style.display = 'flex';
      if (noCardEl) noCardEl.style.display = 'block';
    } else {
      // Show error
      if (errorEl) {
        errorEl.style.display = 'block';
        if (errorMsgEl) {
          errorMsgEl.textContent = e.message || 'Failed to generate virtual card. Please try again.';
        }
      }
      if (noCardEl) noCardEl.style.display = 'block';
    }
  }
}

