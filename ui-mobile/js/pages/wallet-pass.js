export async function initWalletPassPage(rootEl) {
  console.log('[WalletPass] Initializing wallet pass page...');

  rootEl.innerHTML = `
    <style>
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
    </style>
    <div style="padding: 20px; background: white; min-height: calc(100vh - 140px);">
      <div style="margin-bottom: 24px;">
        <h1 style="font-size: 24px; font-weight: 700; color: #111827; margin-bottom: 8px;">Wallet Pass</h1>
        <p style="font-size: 14px; color: #6b7280;">
          Add your Nova balance to Apple Wallet or Google Wallet for quick access
        </p>
      </div>

      <!-- Benefits Card -->
      <div style="background: #f8fafc; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
        <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 12px;">Benefits</h3>
        <ul style="list-style: none; padding: 0; margin: 0;">
          <li style="display: flex; align-items: start; gap: 8px; margin-bottom: 12px; font-size: 14px; color: #374151;">
            <span style="color: #22c55e; font-weight: 600;">✓</span>
            <span>View your Nova balance at a glance</span>
          </li>
          <li style="display: flex; align-items: start; gap: 8px; margin-bottom: 12px; font-size: 14px; color: #374151;">
            <span style="color: #22c55e; font-weight: 600;">✓</span>
            <span>Quick access during charging sessions</span>
          </li>
          <li style="display: flex; align-items: start; gap: 8px; font-size: 14px; color: #374151;">
            <span style="color: #22c55e; font-weight: 600;">✓</span>
            <span>Checkout shortcut at partner merchants</span>
          </li>
        </ul>
      </div>

      <!-- Action Buttons -->
      <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px;">
        <button id="wp-apple-btn" style="background: #000; color: white; border: none; padding: 16px; border-radius: 12px; font-weight: 600; font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
          </svg>
          <span>Add to Apple Wallet</span>
        </button>

        <button id="wp-google-btn" style="background: #4285f4; color: white; border: none; padding: 16px; border-radius: 12px; font-weight: 600; font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          <span>Add to Google Wallet</span>
        </button>
      </div>

      <!-- Info Text -->
      <div style="background: #fef3c7; border: 1px solid #fde68a; border-radius: 8px; padding: 12px; margin-top: 24px;">
        <p style="font-size: 13px; color: #92400e; margin: 0;">
          <strong>Note:</strong> Wallet pass is optional. You can always use your virtual card or scan QR codes to redeem Nova.
        </p>
      </div>

      <!-- Error State -->
      <div id="wp-error" style="display: none; background: #fee2e2; border: 1px solid #fecaca; color: #991b1b; padding: 12px; border-radius: 8px; margin-top: 20px; font-size: 14px;">
        <div id="wp-error-message"></div>
      </div>

      <!-- Success State -->
      <div id="wp-success" style="display: none; background: #d1fae5; border: 1px solid #a7f3d0; color: #065f46; padding: 12px; border-radius: 8px; margin-top: 20px; font-size: 14px;">
      </div>

      <!-- Preview Download Button (shown on error) -->
      <button id="wp-preview-btn" style="display: none; background: #6b7280; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: 600; font-size: 14px; cursor: pointer; margin-top: 12px; width: 100%;">
        Download Preview ZIP
      </button>
    </div>
  `;

  // Wire buttons
  rootEl.querySelector('#wp-apple-btn')?.addEventListener('click', async () => {
    await addToAppleWallet(rootEl);
  });

  rootEl.querySelector('#wp-google-btn')?.addEventListener('click', async () => {
    await addToGoogleWallet(rootEl);
  });
  
  rootEl.querySelector('#wp-preview-btn')?.addEventListener('click', async () => {
    await downloadPreview(rootEl);
  });
}

async function addToAppleWallet(rootEl) {
  const btn = rootEl.querySelector('#wp-apple-btn');
  const errorEl = rootEl.querySelector('#wp-error');
  const errorMsgEl = rootEl.querySelector('#wp-error-message');
  const successEl = rootEl.querySelector('#wp-success');
  const previewBtn = rootEl.querySelector('#wp-preview-btn');
  
  // Hide previous messages
  if (errorEl) errorEl.style.display = 'none';
  if (successEl) successEl.style.display = 'none';
  if (previewBtn) previewBtn.style.display = 'none';
  
  // Set loading state
  const originalText = btn?.textContent || 'Add to Apple Wallet';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `
      <span style="display: inline-block; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: white; border-radius: 50%; animation: spin 0.8s linear infinite;"></span>
      <span>Generating pass...</span>
    `;
  }
  
  try {
    const BASE = window.location.origin;
    const response = await fetch(`${BASE}/v1/wallet/pass/apple/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });

    if (response.status === 501) {
      const error = await response.json();
      const errorCode = error.detail?.error || 'APPLE_WALLET_SIGNING_DISABLED';
      const errorMessage = error.detail?.message || 'Apple Wallet signing is not enabled';
      
      let userMessage = 'Apple Wallet signing is not enabled on this server.';
      
      if (errorCode === 'APPLE_WALLET_SIGNING_MISCONFIGURED') {
        userMessage = `Configuration error: ${errorMessage}`;
      } else if (errorCode === 'APPLE_WALLET_ASSETS_MISSING') {
        userMessage = `Missing assets: ${errorMessage}`;
      }
      
      showError(rootEl, userMessage);
      
      // Show preview download button
      if (previewBtn) {
        previewBtn.style.display = 'block';
        previewBtn.onclick = () => downloadPreview(rootEl);
      }
      
      return;
    }

    if (response.status === 401) {
      showError(rootEl, 'Please log in to create a wallet pass.');
      return;
    }

    if (response.status === 400) {
      const error = await response.json();
      showError(rootEl, error.detail?.message || 'Not eligible for Apple Wallet. Connect your EV first.');
      return;
    }

    if (!response.ok) {
      throw new Error(`Failed to create Apple Wallet pass: ${response.status}`);
    }

    // Download the .pkpass file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nerava-wallet.pkpass';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    // Show success message
    if (successEl) {
      successEl.style.display = 'block';
      successEl.textContent = 'Pass downloaded! Open on iPhone to add to Wallet.';
    }

  } catch (error) {
    console.error('Error adding to Apple Wallet:', error);
    showError(rootEl, 'Failed to add to Apple Wallet. Please try again.');
  } finally {
    // Reset button state
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
        </svg>
        <span>${originalText}</span>
      `;
    }
  }
}

async function downloadPreview(rootEl) {
  const btn = rootEl.querySelector('#wp-preview-btn');
  const errorEl = rootEl.querySelector('#wp-error');
  
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Downloading preview...';
  }
  
  try {
    const BASE = window.location.origin;
    const response = await fetch(`${BASE}/v1/wallet/pass/apple/preview`, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`Failed to download preview: ${response.status}`);
    }

    // Download the ZIP file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nerava-wallet-preview.zip';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    if (errorEl) {
      errorEl.style.display = 'none';
    }
    
  } catch (error) {
    console.error('Error downloading preview:', error);
    showError(rootEl, 'Failed to download preview. Please try again.');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Download Preview ZIP';
    }
  }
}

async function addToGoogleWallet(rootEl) {
  const errorEl = rootEl.querySelector('#wp-error');
  const errorMsgEl = rootEl.querySelector('#wp-error-message');
  
  try {
    const BASE = window.location.origin;
    const response = await fetch(`${BASE}/v1/wallet/pass/google/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });

    if (response.status === 501) {
      const error = await response.json();
      showError(rootEl, 'Google Wallet not enabled yet. ' + (error.detail?.message || ''));
      return;
    }

    if (response.status === 400) {
      const error = await response.json();
      showError(rootEl, error.detail?.message || 'Not eligible for Google Wallet.');
      return;
    }

    if (!response.ok) {
      throw new Error('Failed to create Google Wallet pass');
    }

    const data = await response.json();
    
    // Google Wallet returns a link/URL to add the pass
    if (data.add_link) {
      window.open(data.add_link, '_blank');
    } else {
      showError(rootEl, 'Google Wallet pass created, but no add link was returned.');
    }

  } catch (error) {
    console.error('Error adding to Google Wallet:', error);
    showError(rootEl, 'Failed to add to Google Wallet. Please try again.');
  }
}

function showError(rootEl, message) {
  const errorEl = rootEl.querySelector('#wp-error');
  const errorMsgEl = rootEl.querySelector('#wp-error-message');
  const successEl = rootEl.querySelector('#wp-success');
  
  if (errorEl && errorMsgEl) {
    errorMsgEl.textContent = message;
    errorEl.style.display = 'block';
    
    // Hide success message if shown
    if (successEl) {
      successEl.style.display = 'none';
    }
    
    // Don't auto-hide errors (user might want to read them)
  }
}

