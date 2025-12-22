import { apiWalletSummary } from '../core/api.js';
import { formatHoursMinutes, formatUsdFromCents } from '../core/format.js';
import { loadDemoRedemption } from '../core/demo-state.js';
import { setTab } from '../app.js';

// Module-scope state for single-owner polling
let walletPollInterval = null;
let walletCountdownInterval = null;
let walletRefreshCheckInterval = null;
let walletAbortController = null; // For fetch abort if needed
let consecutiveErrors = 0;
const MAX_POLL_ERRORS = 3;

// Hard-stop cleanup function (idempotent)
function stopWalletTimers() {
  if (walletPollInterval) {
    clearInterval(walletPollInterval);
    walletPollInterval = null;
  }
  if (walletCountdownInterval) {
    clearInterval(walletCountdownInterval);
    walletCountdownInterval = null;
  }
  if (walletRefreshCheckInterval) {
    clearInterval(walletRefreshCheckInterval);
    walletRefreshCheckInterval = null;
  }
  if (walletAbortController) {
    try {
      walletAbortController.abort();
    } catch {}
    walletAbortController = null;
  }
}

// Tier colors for battery icon (exact spec)
const TIER_COLORS = {
  Bronze: '#78716c',
  Silver: '#64748b',
  Gold: '#eab308',
  Platinum: '#06b6d4'
};

// Format date as MM/DD/YY
function formatDateMMDDYY(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const year = String(date.getFullYear()).slice(-2);
  return `${month}/${day}/${year}`;
}

// Map activity title from type/reason
function getActivityTitle(item, summary) {
  const type = item.type || '';
  const reason = item.reason || '';

  // Charging session - always show "Charging Session" like in the design
  if (type === 'charging_session') {
    return 'Charging Session';
  }

  // Nova transactions
  if (type === 'nova_transaction') {
    if (item.transaction_type === 'driver_earn') {
      return 'Nova Earned';
    }
    return 'Nova Transaction';
  }

  // Wallet transaction mappings
  if (type === 'wallet_transaction') {
    if (reason === 'REDEEM') {
      return 'Nova Redeemed';
    }
    if (reason === 'DRIVER_EARN' || reason === 'OFF_PEAK_AWARD') {
      return 'Nova Earned';
    }
    if (reason === 'ADMIN_GRANT') {
      return 'Bonus Nova';
    }
  }

  // Fallback: prettify reason or type
  if (reason) {
    return reason.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
  if (type) {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  return 'Activity';
}

// Format activity amount as USD
function formatActivityAmount(item, summary) {
  const conversionRate = summary?.conversion_rate_cents ?? 10;
  
  // Handle aggregated daily charging sessions
  if (item.type === 'charging_session' && item.aggregation === 'daily') {
    // Prefer amount_cents if provided (already calculated on backend), otherwise calculate from nova_earned
    const cents = item.amount_cents !== undefined 
      ? Math.abs(item.amount_cents)
      : (item.nova_earned !== undefined ? item.nova_earned * conversionRate : 0);
    return {
      text: `+${formatUsdFromCents(cents)}`,
      isCredit: true
    };
  }
  
  // Handle aggregated daily Nova transactions
  if (item.type === 'nova_transaction' && item.aggregation === 'daily' && item.transaction_type === 'driver_earn') {
    // Prefer amount_cents if provided (already calculated on backend), otherwise calculate from amount
    const cents = item.amount_cents !== undefined 
      ? Math.abs(item.amount_cents)
      : (item.amount !== undefined ? item.amount * conversionRate : 0);
    return {
      text: `+${formatUsdFromCents(cents)}`,
      isCredit: true
    };
  }
  
  // Try all known amount fields in order of preference
  const raw =
    item.amount_cents ??
    item.nova_delta ??
    item.nova_amount ??
    item.amount ??
    item.nova_earned ??
    item.reward_nova ??
    null;
  
  if (raw !== null && raw !== undefined && raw !== 0) {
    // If amount_cents is explicitly set, use it directly; otherwise convert from Nova
    const cents =
      item.amount_cents !== undefined
        ? Math.abs(raw)
        : Math.abs(raw) * conversionRate;
    
    return {
      text: `${raw >= 0 ? '+' : '-'}${formatUsdFromCents(cents)}`,
      isCredit: raw >= 0
    };
  }
  
  // Explicit UI fallback for legacy charging sessions with missing reward fields
  if (item.type === 'charging_session') {
    return {
      text: '+$0.01',
      isCredit: true,
      _fallback: true // DEBUG marker
    };
  }
  
  return null;
}

// Battery icon SVG (inline) - uses fill for tier color
function getBatteryIconSVG(color) {
  return `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="7" width="16" height="10" rx="2" ry="2" fill="${color}"/>
      <line x1="6" y1="11" x2="6" y2="13" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="18" y1="11" x2="18" y2="13" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M22 11v2" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
  `;
}

export async function initWalletPage(rootEl) {
  console.log('[Wallet] Initializing wallet page...');

  // Stop any existing timers before starting new ones (prevents duplicates)
  stopWalletTimers();

  let currentWindowEndsInSeconds = 0;
  let previousReputationPoints = null; // Track previous reputation points for animation
  
  // Expose test function for debugging (can be called from console)
  // Helper function to ensure progress bar is visible
  const ensureProgressBarVisible = (el, progressPercent) => {
    if (!el) {
      console.error('[Wallet] Progress bar element not found for visibility fix');
      return;
    }
    el.style.setProperty('display', 'block', 'important');
    el.style.setProperty('opacity', '1', 'important');
    el.style.setProperty('visibility', 'visible', 'important');
    el.style.setProperty('height', '100%', 'important');
    if (progressPercent === 0) {
      el.style.setProperty('min-width', '2px', 'important');
      el.style.setProperty('width', '0%', 'important');
    } else {
      el.style.removeProperty('min-width');
      el.style.setProperty('width', `${progressPercent}%`, 'important');
    }
    console.log('[Wallet] Progress bar visibility ensured:', {
      width: el.style.width,
      minWidth: el.style.minWidth,
      display: window.getComputedStyle(el).display,
      opacity: window.getComputedStyle(el).opacity,
      visibility: window.getComputedStyle(el).visibility,
      height: window.getComputedStyle(el).height
    });
  };
  
  // Expose fix function for manual use
  window.fixProgressBarVisibility = () => {
    const tierProgressEl = rootEl.querySelector('#w-tier-progress');
    const containerEl = tierProgressEl?.parentElement;
    const reputationEl = rootEl.querySelector('#wallet-reputation');
    
    console.log('[Wallet] 🔧 Fixing progress bar visibility...');
    console.log('[Wallet] Element search results:', {
      progressBar: !!tierProgressEl,
      container: !!containerEl,
      reputation: !!reputationEl
    });
    
    if (!tierProgressEl) {
      console.error('[Wallet] ❌ Progress bar element (#w-tier-progress) not found!');
      console.log('[Wallet] Available elements in wallet-reputation:', 
        reputationEl ? Array.from(reputationEl.querySelectorAll('*')).map(el => ({
          id: el.id,
          className: el.className,
          tagName: el.tagName
        })) : 'reputation element not found'
      );
      return;
    }
    
    // Check container
    if (containerEl) {
      const containerStyle = window.getComputedStyle(containerEl);
      console.log('[Wallet] Container state:', {
        width: containerStyle.width,
        height: containerStyle.height,
        overflow: containerStyle.overflow,
        display: containerStyle.display,
        visibility: containerStyle.visibility
      });
      
      // Ensure container is visible
      containerEl.style.setProperty('display', 'block', 'important');
      containerEl.style.setProperty('visibility', 'visible', 'important');
      containerEl.style.setProperty('height', '8px', 'important');
      containerEl.style.setProperty('overflow', 'visible', 'important'); // Temporarily to see the bar
    }
    
    // Get current progress
    const currentWidth = tierProgressEl.style.width || '0%';
    const progressMatch = currentWidth.match(/(\d+(?:\.\d+)?)%/);
    const progressPercent = progressMatch ? parseFloat(progressMatch[1]) : 0;
    
    console.log('[Wallet] Current state:', {
      inlineWidth: tierProgressEl.style.width,
      computedWidth: window.getComputedStyle(tierProgressEl).width,
      progressPercent
    });
    
    // Force visibility with a more aggressive approach
    tierProgressEl.style.setProperty('display', 'block', 'important');
    tierProgressEl.style.setProperty('opacity', '1', 'important');
    tierProgressEl.style.setProperty('visibility', 'visible', 'important');
    tierProgressEl.style.setProperty('height', '100%', 'important');
    tierProgressEl.style.setProperty('background', '#78716c', 'important'); // Bronze color
    
    // For 0% progress, make it clearly visible
    if (progressPercent === 0 || !progressMatch) {
      tierProgressEl.style.setProperty('min-width', '8px', 'important'); // Make it more visible
      tierProgressEl.style.setProperty('width', '8px', 'important'); // Set to 8px instead of 0%
      console.log('[Wallet] ✅ Set to 8px width for visibility (progress is 0%)');
    } else {
      tierProgressEl.style.removeProperty('min-width');
      tierProgressEl.style.setProperty('width', `${progressPercent}%`, 'important');
      console.log('[Wallet] ✅ Set to', progressPercent + '% width');
    }
    
    // Force a reflow
    void tierProgressEl.offsetWidth;
    
    // Log final state
    const finalStyle = window.getComputedStyle(tierProgressEl);
    console.log('[Wallet] ✅ Final state:', {
      inlineWidth: tierProgressEl.style.width,
      computedWidth: finalStyle.width,
      minWidth: tierProgressEl.style.minWidth || finalStyle.minWidth,
      display: finalStyle.display,
      opacity: finalStyle.opacity,
      visibility: finalStyle.visibility,
      height: finalStyle.height,
      backgroundColor: finalStyle.backgroundColor
    });
    
    // Restore container overflow after a moment
    if (containerEl) {
      setTimeout(() => {
        containerEl.style.setProperty('overflow', 'hidden', 'important');
        console.log('[Wallet] Container overflow restored to hidden');
      }, 1000);
    }
  };
  
  window.testReputationAnimation = () => {
    const tierProgressEl = rootEl.querySelector('#w-tier-progress');
    const containerEl = tierProgressEl?.parentElement;
    
    if (!tierProgressEl) {
      console.error('[Wallet][Test] Progress bar element not found!');
      return;
    }
    
    // Get the actual current progress from the wallet summary (if available)
    // This will be used to restore the correct value after the test
    const currentProgressPercent = (() => {
      const currentWidth = tierProgressEl.style.width;
      if (currentWidth && currentWidth !== '0%') {
        const match = currentWidth.match(/(\d+(?:\.\d+)?)%/);
        if (match) return parseFloat(match[1]);
      }
      // Fallback: try to get from computed style
      const computed = window.getComputedStyle(tierProgressEl).width;
      const containerWidth = containerEl ? parseFloat(window.getComputedStyle(containerEl).width) : 366;
      if (computed && containerWidth > 0) {
        const widthPx = parseFloat(computed);
        return (widthPx / containerWidth) * 100;
      }
      return 0; // Default to 0% if we can't determine
    })();
    
    console.log('[Wallet][Test] 🎬 Triggering test animation...');
    console.log('[Wallet][Test] Current progress:', currentProgressPercent + '%');
    console.log('[Wallet][Test] Element:', tierProgressEl);
    
    // Store original styles to restore later
    const originalHeight = tierProgressEl.style.height;
    const originalMinWidth = tierProgressEl.style.minWidth;
    const originalTransition = tierProgressEl.style.transition;
    
    // Make progress bar taller temporarily for visibility
    tierProgressEl.style.setProperty('height', '16px', 'important');
    if (containerEl) {
      const containerOriginalHeight = containerEl.style.height;
      containerEl.style.setProperty('height', '16px', 'important');
    }
    
    const beforeWidth = window.getComputedStyle(tierProgressEl).width;
    console.log('[Wallet][Test] Before:', { computedWidth: beforeWidth, inlineWidth: tierProgressEl.style.width });
    
    // Step 1: Force immediate reset to 0% (no transition)
    tierProgressEl.style.setProperty('transition', 'none', 'important');
    tierProgressEl.style.setProperty('width', '0%', 'important');
    tierProgressEl.style.setProperty('min-width', '0px', 'important');
    
    // Force browser to apply the change
    void tierProgressEl.offsetWidth;
    
    console.log('[Wallet][Test] ✅ Reset to 0%, now animating to 100%...');
    
    // Step 2: Now animate to 100%
    setTimeout(() => {
      tierProgressEl.style.setProperty('transition', 'width 1.2s cubic-bezier(0.4, 0, 0.2, 1)', 'important');
      tierProgressEl.style.setProperty('width', '100%', 'important');
      void tierProgressEl.offsetWidth; // Force reflow
      
      console.log('[Wallet][Test] ⏳ Animating to 100%... (should see bar filling)');
      
      // Step 3: After filling, animate back to actual progress (or 50% for test)
      setTimeout(() => {
        const targetPercent = currentProgressPercent > 0 ? currentProgressPercent : 50; // Use actual or 50% for test
        console.log('[Wallet][Test] ⏳ Now animating back to', targetPercent + '% with bounce...');
        tierProgressEl.style.setProperty('transition', 'width 1.5s cubic-bezier(0.34, 1.56, 0.64, 1)', 'important');
        tierProgressEl.style.setProperty('width', `${targetPercent}%`, 'important');
        void tierProgressEl.offsetWidth; // Force reflow
        
        setTimeout(() => {
          const afterWidth = window.getComputedStyle(tierProgressEl).width;
          console.log('[Wallet][Test] ✅ Animation complete!');
          console.log('[Wallet][Test] Final:', { computedWidth: afterWidth, inlineWidth: tierProgressEl.style.width });
          
          // Restore original styles
          if (originalHeight) {
            tierProgressEl.style.height = originalHeight;
          } else {
            tierProgressEl.style.removeProperty('height');
          }
          
          // Restore transition to normal
          tierProgressEl.style.setProperty('transition', 'width 0.3s ease-out', 'important');
          
          // Restore container height
          if (containerEl) {
            containerEl.style.removeProperty('height');
          }
          
          // Ensure the progress bar is visible - set min-width for 0% progress
          if (targetPercent === 0) {
            tierProgressEl.style.setProperty('min-width', '2px', 'important');
          } else {
            tierProgressEl.style.removeProperty('min-width');
          }
          
          // Make sure width is set correctly
          tierProgressEl.style.setProperty('width', `${targetPercent}%`, 'important');
          
          console.log('[Wallet][Test] ✅ Styles restored, progress bar should be visible at', targetPercent + '%');
          console.log('[Wallet][Test] Final state:', {
            width: tierProgressEl.style.width,
            minWidth: tierProgressEl.style.minWidth,
            computedWidth: window.getComputedStyle(tierProgressEl).width
          });
          
          // Ensure progress bar is visible before reloading
          const finalProgress = currentProgressPercent > 0 ? currentProgressPercent : 0;
          ensureProgressBarVisible(tierProgressEl, finalProgress);
          
          // Reload wallet summary to restore actual progress values
          console.log('[Wallet][Test] Reloading wallet summary to restore actual values...');
          setTimeout(() => {
            if (typeof loadWalletSummary === 'function') {
              loadWalletSummary(true).catch(err => {
                console.error('[Wallet][Test] Error reloading wallet summary:', err);
                // If reload fails, at least ensure visibility
                ensureProgressBarVisible(tierProgressEl, finalProgress);
              });
            } else {
              // If loadWalletSummary isn't available, just ensure visibility
              ensureProgressBarVisible(tierProgressEl, finalProgress);
            }
          }, 100);
        }, 1500);
      }, 1200);
    }, 100);
  };

  // Cleanup function (will be enhanced after loadWalletSummary is defined)
  let cleanup = () => {
    stopWalletTimers();
  };
  
  // Store handleWalletInvalidate for cleanup (will be set after loadWalletSummary is defined)
  let handleWalletInvalidate = null;

  // Check if this is a payment success redirect
  const urlParams = new URLSearchParams(window.location.search);
  const paidParam = urlParams.get('paid');
  const isPaymentSuccess = paidParam !== null;

  // Check offline status
  const isOffline = typeof navigator !== 'undefined' && navigator.onLine === false;

  // Initial render with loading skeleton
  rootEl.innerHTML = `
    <div style="padding: 20px; padding-bottom: calc(20px + 84px + env(safe-area-inset-bottom, 0px)); background: white; height: calc(100vh - 52px - var(--tabbar-height, 76px)); overflow-y: auto; overflow-x: hidden; display: flex; flex-direction: column;">
      <div style="flex-shrink: 0;">
        ${isPaymentSuccess ? `
          <div style="background: #dcfce7; border: 1px solid #22c55e; color: #166534; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-weight: 600;">
            🎉 Payment completed! You earned rewards for this purchase.
          </div>
        ` : ''}
        
        ${isOffline ? `
          <div id="wallet-offline-badge" style="background: #fef3c7; border: 1px solid #f59e0b; color: #92400e; padding: 8px 12px; border-radius: 8px; margin-bottom: 16px; font-size: 13px; font-weight: 600; text-align: center;">
            📡 Offline - Showing last known data
          </div>
        ` : ''}
        
        <!-- Error Alert (hidden by default) -->
        <div id="wallet-error-alert" style="display: none; background: #fee2e2; border: 1px solid #ef4444; color: #991b1b; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-weight: 600; cursor: pointer;">
          Unable to load wallet. Tap to retry.
        </div>
        
        <!-- Retry Banner (hidden by default, shown after polling stops) -->
        <div id="wallet-retry-banner" style="display: none; background: #fef3c7; border: 1px solid #f59e0b; color: #92400e; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-weight: 600; cursor: pointer; text-align: center;">
          Wallet temporarily unavailable. Tap to retry.
        </div>
        
        <!-- Off-peak Banner Bar -->
        <div id="wallet-offpeak-banner" style="display: none; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-weight: 600; font-size: 14px; text-align: center;">
          <span id="wallet-offpeak-text">⚡ Loading...</span>
        </div>
        
        <!-- Blue Balance Card -->
        <div id="wallet-balance-card" class="wallet-card" style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); border-radius: 16px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);">
          <div class="wallet-card-content">
            <div style="font-size: 13px; color: rgba(255, 255, 255, 0.8); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">
              Nova Balance
            </div>
            <div id="wallet-usd-balance" style="font-size: 42px; font-weight: bold; color: #ffffff; margin-bottom: 8px; line-height: 1;">
              $0.00
            </div>
            <div id="wallet-nova-balance" style="font-size: 16px; color: rgba(255, 255, 255, 0.9);">
              0 Nova
            </div>
          </div>
        </div>
        
        <!-- Quick Actions -->
        <div style="display: flex; gap: 8px; margin-bottom: 20px;">
          <button id="w-generate-card" style="flex: 1; background: #3b82f6; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: 600; font-size: 14px;">
            Download Wallet Pass
          </button>
          <button id="w-redeem-btn" style="flex: 1; background: #f1f5f9; color: #0f172a; border: none; padding: 12px; border-radius: 8px; font-weight: 600; font-size: 14px;">
            Redeem Nova
          </button>
        </div>
        
        <!-- Energy Reputation with Battery Icon -->
        <div id="wallet-reputation" style="background: white; border-radius: 12px; padding: 16px; margin-bottom: 20px; border: 1px solid #e2e8f0;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span id="wallet-battery-icon" style="display: inline-flex; align-items: center;">
              ${getBatteryIconSVG(TIER_COLORS.Bronze)}
            </span>
            <span style="font-size: 14px; font-weight: 600; color: #374151;">Energy Reputation</span>
            <span id="w-tier-badge" style="margin-left: auto; color: #374151; font-size: 13px; font-weight: 600;">Loading...</span>
          </div>
          <div style="background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 4px; position: relative;">
            <div id="w-tier-progress" style="background: ${TIER_COLORS.Bronze}; height: 100%; width: 0%; min-width: 2px; transition: width 0.3s ease-out; will-change: width; display: block; opacity: 1; visibility: visible;"></div>
          </div>
          <div class="tier-meta-row">
            <span id="w-tier-next" style="font-size: 12px; color: #6b7280;">Loading...</span>
            <span id="w-charging-indicator" class="charging-indicator">
              <span class="charging-dot"></span>
              Charging Detected
            </span>
          </div>
        </div>
      </div>
      
      <!-- Recent Activity -->
      <div style="background: white; border-radius: 12px; padding: 16px; margin-bottom: 20px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; flex: 1; min-height: 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-shrink: 0;">
          <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin: 0;">Recent Activity</h3>
          <a href="#/activity" style="font-size: 14px; font-weight: 600; color: #3b82f6; text-decoration: none;">View all</a>
        </div>
        <ul id="wallet-activity-list" style="list-style: none; padding: 0; margin: 0; flex: 1; overflow-y: auto; overflow-x: hidden; -webkit-overflow-scrolling: touch; min-height: 0;">
          <li style="padding: 12px 0; color: #9ca3af; font-size: 14px; text-align: center;">Loading activity...</li>
        </ul>
      </div>
    </div>
  `;

  // Function to update UI from summary data
  const updateUI = (summary) => {
    if (!summary) return;

    // Update balance card
    const usdBalanceEl = rootEl.querySelector('#wallet-usd-balance');
    const novaBalanceEl = rootEl.querySelector('#wallet-nova-balance');
    const balanceCardEl = rootEl.querySelector('#wallet-balance-card');
    
    if (usdBalanceEl) {
      usdBalanceEl.textContent = summary.usd_equivalent || '$0.00';
    }
    if (novaBalanceEl) {
      const novaBalance = summary.nova_balance || 0;
      novaBalanceEl.textContent = `${novaBalance.toLocaleString()} Nova`;
    }
    
    // Add charging glow class
    if (balanceCardEl) {
      if (summary.charging_detected) {
        balanceCardEl.classList.add('wallet-card-charging');
      } else {
        balanceCardEl.classList.remove('wallet-card-charging');
      }
    }

    // Update off-peak banner
    const offpeakBannerEl = rootEl.querySelector('#wallet-offpeak-banner');
    const offpeakTextEl = rootEl.querySelector('#wallet-offpeak-text');
    if (offpeakBannerEl && offpeakTextEl) {
      currentWindowEndsInSeconds = summary.window_ends_in_seconds || 0;
      const timeStr = formatHoursMinutes(currentWindowEndsInSeconds);
      
      if (summary.offpeak_active) {
        offpeakBannerEl.style.display = 'block';
        offpeakBannerEl.style.background = '#dcfce7';
        offpeakBannerEl.style.border = '1px solid #22c55e';
        offpeakBannerEl.style.color = '#166534';
        offpeakTextEl.textContent = `⚡ Off-peak charging ends in ${timeStr}`;
      } else {
        offpeakBannerEl.style.display = 'block';
        offpeakBannerEl.style.background = '#fee2e2';
        offpeakBannerEl.style.border = '1px solid #ef4444';
        offpeakBannerEl.style.color = '#991b1b';
        offpeakTextEl.textContent = `⚡ Expensive charging ends in ${timeStr}`;
      }
    }

    // Update reputation (use backend-computed values - backend is source of truth)
    const rep = summary.reputation || {};
    const tier = rep.tier || 'Bronze';
    const tierColor = rep.tier_color || TIER_COLORS[tier] || TIER_COLORS.Bronze;
    const pointsToNext = rep.points_to_next;
    const nextTier = rep.next_tier;
    const currentReputationPoints = rep.points || 0;
    
    // Use backend progress_to_next directly (0.0-1.0, not rounded server-side)
    // Only fallback to 0 if backend value is missing (defensive)
    let progress = rep.progress_to_next;
    if (progress === null || progress === undefined || isNaN(progress)) {
      progress = 0.0;  // Defensive fallback only
    }
    // Clamp progress to valid range (0-1)
    progress = Math.max(0.0, Math.min(1.0, progress));
    
    const tierBadgeEl = rootEl.querySelector('#w-tier-badge');
    const tierProgressEl = rootEl.querySelector('#w-tier-progress');
    const tierNextEl = rootEl.querySelector('#w-tier-next');
    const batteryIconEl = rootEl.querySelector('#wallet-battery-icon');
    
    // Log reputation data with change detection
    const pointsChanged = previousReputationPoints !== null && currentReputationPoints !== previousReputationPoints;
    console.log('[Wallet][Reputation] Reputation data:', {
      points: currentReputationPoints,
      tier,
      pointsToNext,
      nextTier,
      progress: progress,
      progressPercent: Math.round(progress * 100) + '%',
      previousPoints: previousReputationPoints,
      pointsChanged,
      pointsDelta: pointsChanged ? (currentReputationPoints - previousReputationPoints) : 0
    });
    
    // Detect if reputation points increased (for celebration animation)
    const reputationIncreased = previousReputationPoints !== null && 
                                 currentReputationPoints > previousReputationPoints;
    
    // Log for debugging
    if (previousReputationPoints !== null) {
      console.log('[Wallet][Reputation] Point comparison:', {
        previous: previousReputationPoints,
        current: currentReputationPoints,
        increased: reputationIncreased,
        delta: currentReputationPoints - previousReputationPoints
      });
    }
    
    if (tierBadgeEl) {
      tierBadgeEl.textContent = tier;
      tierBadgeEl.style.color = tierColor;
    }
    
    if (tierProgressEl) {
      // Set progress bar width (0-100%) from backend progress_to_next
      const progressPercent = Math.min(100, Math.max(0, Math.round(progress * 100)));
      console.log('[Wallet][Reputation] Setting progress bar:', { 
        progress, 
        progressPercent, 
        tierColor,
        elementFound: true,
        currentWidth: tierProgressEl.style.width,
        previousPoints: previousReputationPoints,
        currentPoints: currentReputationPoints,
        reputationIncreased
      });
      
      // If reputation increased, trigger celebration animation
      if (reputationIncreased) {
        console.log('[Wallet][Reputation] 🎉 Reputation increased! Triggering celebration animation', {
          previous: previousReputationPoints,
          current: currentReputationPoints,
          progressPercent,
          increase: currentReputationPoints - previousReputationPoints
        });
        
        // Store current width before animation
        const currentWidth = tierProgressEl.style.width || '0%';
        console.log('[Wallet][Reputation] 🎉 Starting celebration animation from', currentWidth, 'to', progressPercent + '%');
        
        // Celebration animation: fill to 100%, then animate back to actual progress
        // Step 1: Remove transition temporarily to set initial state
        tierProgressEl.style.transition = 'none';
        tierProgressEl.style.width = currentWidth;
        tierProgressEl.offsetHeight; // Force reflow to ensure style is applied
        
        // Step 2: Use requestAnimationFrame to ensure DOM is updated
        requestAnimationFrame(() => {
          console.log('[Wallet][Reputation] Step 1: Animating to 100%...');
          // Step 3: Animate to 100%
          tierProgressEl.style.transition = 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
          tierProgressEl.style.width = '100%';
          tierProgressEl.offsetHeight; // Force reflow
          
          // Step 4: After filling to 100%, animate back to actual progress with bounce
          setTimeout(() => {
            console.log('[Wallet][Reputation] Step 2: Animating back to', progressPercent + '%...');
            requestAnimationFrame(() => {
              tierProgressEl.style.transition = 'width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)'; // Bounce effect
              tierProgressEl.style.width = `${progressPercent}%`;
              tierProgressEl.offsetHeight; // Force reflow
              console.log('[Wallet][Reputation] ✅ Animation complete, set to', progressPercent + '%');
            });
          }, 600);
        });
      } else {
        // Normal update with smooth transition
        const currentWidth = tierProgressEl.style.width || '0%';
        if (currentWidth !== `${progressPercent}%`) {
          tierProgressEl.style.transition = 'width 0.3s ease-out';
          tierProgressEl.style.width = `${progressPercent}%`;
        }
      }
      
      tierProgressEl.style.background = tierColor;
      
      // Ensure element is visible even at 0% (for debugging/visual feedback)
      // Always set min-width explicitly to ensure visibility
      if (progressPercent === 0) {
        tierProgressEl.style.setProperty('min-width', '2px', 'important');
        tierProgressEl.style.setProperty('width', '0%', 'important');
        console.log('[Wallet][Reputation] Progress is 0%, setting min-width to 2px for visibility');
      } else {
        tierProgressEl.style.removeProperty('min-width');
        // Width is already set above in the animation or normal update
      }
      
      // Ensure the element is actually visible (defensive)
      tierProgressEl.style.setProperty('display', 'block', 'important');
      tierProgressEl.style.setProperty('opacity', '1', 'important');
      tierProgressEl.style.setProperty('visibility', 'visible', 'important');
      tierProgressEl.style.setProperty('height', '100%', 'important');
      
      // Log final state for debugging
      const finalComputed = window.getComputedStyle(tierProgressEl);
      console.log('[Wallet][Reputation] Progress bar final state:', {
        inlineWidth: tierProgressEl.style.width,
        computedWidth: finalComputed.width,
        minWidth: tierProgressEl.style.minWidth,
        display: finalComputed.display,
        opacity: finalComputed.opacity,
        visibility: finalComputed.visibility,
        height: finalComputed.height
      });
    } else {
      console.warn('[Wallet][Reputation] Progress bar element not found!');
    }
    
    if (tierNextEl) {
      // Use backend points_to_next and next_tier directly
      if (pointsToNext !== null && pointsToNext !== undefined && nextTier) {
        const text = `${pointsToNext} Nova to ${nextTier}`;
        const previousText = tierNextEl.textContent;
        tierNextEl.textContent = text;
        
        // Log if the value changed
        if (previousText !== text) {
          console.log('[Wallet][Reputation] ✅ "Nova to next" updated:', {
            previous: previousText,
            new: text,
            pointsToNext,
            nextTier,
            reputationPoints: currentReputationPoints
          });
        } else {
          console.log('[Wallet][Reputation] "Nova to next" unchanged:', { text, pointsToNext, nextTier });
        }
      } else {
        // Max tier reached (Platinum) or backend didn't provide values
        tierNextEl.textContent = 'Max tier reached';
        console.log('[Wallet][Reputation] Max tier reached (Platinum)');
      }
    } else {
      console.warn('[Wallet][Reputation] "pts to next" element not found!');
    }
    
    // Update previous reputation points for next comparison
    previousReputationPoints = currentReputationPoints;
    
    // Toggle charging indicator
    const indicator = rootEl.querySelector('#w-charging-indicator');
    if (indicator) {
      indicator.style.display = summary.charging_detected ? 'flex' : 'none';
    }
    
    if (batteryIconEl) {
      batteryIconEl.innerHTML = getBatteryIconSVG(tierColor);
    }

    // Update activity list
    const activityListEl = rootEl.querySelector('#wallet-activity-list');
    if (activityListEl) {
      const activities = summary.recent_activity || [];
      console.log('[Wallet][Activity] Raw items:', activities);
      console.log('[Wallet][Activity] Activity count:', activities.length);

      if (activities.length > 0) {
        try {
          const activityHtml = activities.map((item, index) => {
            console.log(`[Wallet][Activity] Processing item ${index}:`, item);

            // Get title - always use simple titles like in the design
            let title = 'Charging Session';
            if (item.type === 'charging_session') {
              title = 'Charging Session';
            } else if (item.type === 'nova_transaction') {
              title = item.transaction_type === 'driver_earn' ? 'Nova Earned' : 'Nova Transaction';
            } else if (item.type === 'wallet_transaction') {
              title = item.reason === 'REDEEM' ? 'Nova Redeemed' : 'Nova Earned';
            }

            // Get amount info
            const amountInfo = formatActivityAmount(item, summary);

            // Simple subtitle like in the design
            let subtitle = 'Nova issued';
            if (item.type === 'nova_transaction' || item.type === 'wallet_transaction') {
              subtitle = amountInfo?.isCredit ? 'Nova earned' : 'Nova spent';
            }

            // Build the HTML with explicit inline styles
            const amountHtml = amountInfo
              ? `<div style="font-size: 14px; font-weight: 600; color: ${amountInfo.isCredit ? '#22c55e' : '#ef4444'}; white-space: nowrap;">${amountInfo.text}</div>`
              : '';

            return `<li style="display: flex !important; flex-direction: row !important; justify-content: space-between !important; align-items: center !important; padding: 12px 0; border-bottom: 1px solid #f3f4f6; list-style: none;"><div style="flex: 1;"><div style="font-size: 14px; font-weight: 500; color: #111827; margin-bottom: 2px;">${title}</div><div style="font-size: 12px; color: #6b7280;">${subtitle}</div></div>${amountHtml}</li>`;
          }).join('');

          console.log('[Wallet][Activity] Generated HTML length:', activityHtml.length);
          activityListEl.innerHTML = activityHtml;
        } catch (err) {
          console.error('[Wallet][Activity] Error rendering activities:', err);
          activityListEl.innerHTML = '<li style="padding: 12px 0; color: #ef4444; font-size: 14px; text-align: center;">Error loading activity</li>';
        }
      } else {
        activityListEl.innerHTML = '<li style="padding: 12px 0; color: #9ca3af; font-size: 14px; text-align: center;">No activity yet</li>';
      }
    }
  };

  // Function to update countdown
  const updateCountdown = () => {
    if (currentWindowEndsInSeconds > 0) {
      currentWindowEndsInSeconds -= 60; // Decrement by 60 seconds (1 minute)
      const offpeakTextEl = rootEl.querySelector('#wallet-offpeak-text');
      const offpeakBannerEl = rootEl.querySelector('#wallet-offpeak-banner');
      
      if (offpeakTextEl && offpeakBannerEl && offpeakBannerEl.style.display !== 'none') {
        const timeStr = formatHoursMinutes(currentWindowEndsInSeconds);
        const isOffpeak = offpeakBannerEl.style.background.includes('dcfce7');
        
        if (isOffpeak) {
          offpeakTextEl.textContent = `⚡ Off-peak charging ends in ${timeStr}`;
        } else {
          offpeakTextEl.textContent = `⚡ Expensive charging ends in ${timeStr}`;
        }
        
        // If countdown hits 0, refetch summary
        if (currentWindowEndsInSeconds <= 0) {
          loadWalletSummary();
        }
      }
    }
  };

  // Function to load wallet summary
  const loadWalletSummary = async (forceRefresh = false) => {
    const errorAlertEl = rootEl.querySelector('#wallet-error-alert');
    const offlineBadgeEl = rootEl.querySelector('#wallet-offline-badge');
    
    // Hide error alert initially
    if (errorAlertEl) {
      errorAlertEl.style.display = 'none';
    }
    
    // Check offline status
    const isOfflineNow = typeof navigator !== 'undefined' && navigator.onLine === false;
    if (isOfflineNow && offlineBadgeEl) {
      offlineBadgeEl.style.display = 'block';
    } else if (offlineBadgeEl) {
      offlineBadgeEl.style.display = 'none';
    }
    
    // If offline, don't try to fetch
    if (isOfflineNow) {
      return;
    }

    try {
      // Check for demo state first (but skip if forceRefresh is true)
      if (!forceRefresh) {
        const demo = loadDemoRedemption();
        if (demo && typeof demo.wallet_nova_balance === 'number' && demo.wallet_nova_balance > 0) {
          // Use demo data
          // Calculate reputation properly for demo data
          const demoRepScore = demo.reputation_score || 0;
          const TIER_THRESHOLDS_DEMO = {
            Bronze: 0,
            Silver: 100,
            Gold: 300,
            Platinum: 700
          };
          
          // Determine current tier
          let demoTier = 'Bronze';
          let demoNextTier = 'Silver';
          if (demoRepScore >= 700) {
            demoTier = 'Platinum';
            demoNextTier = null;
          } else if (demoRepScore >= 300) {
            demoTier = 'Gold';
            demoNextTier = 'Platinum';
          } else if (demoRepScore >= 100) {
            demoTier = 'Silver';
            demoNextTier = 'Gold';
          }
          
          // Calculate progress
          const currentTierMin = TIER_THRESHOLDS_DEMO[demoTier] || 0;
          const nextTierMin = demoNextTier ? (TIER_THRESHOLDS_DEMO[demoNextTier] || currentTierMin) : currentTierMin;
          let demoProgress = 0;
          if (demoNextTier && nextTierMin > currentTierMin) {
            const pointsInCurrentTier = Math.max(0, demoRepScore - currentTierMin);
            const pointsNeededForNext = nextTierMin - currentTierMin;
            demoProgress = Math.min(1.0, Math.max(0, pointsInCurrentTier / pointsNeededForNext));
          } else {
            demoProgress = 1.0; // Max tier
          }
          
          const demoSummary = {
            nova_balance: demo.wallet_nova_balance,
            nova_balance_cents: demo.wallet_nova_balance * 10,
            conversion_rate_cents: 10,
            usd_equivalent: formatUsdFromCents(demo.wallet_nova_balance * 10),
            charging_detected: false,
            offpeak_active: false,
            window_ends_in_seconds: 3600,
            reputation: {
              tier: demoTier,
              tier_color: TIER_COLORS[demoTier] || TIER_COLORS.Bronze,
              points: demoRepScore,
              next_tier: demoNextTier,
              points_to_next: demoNextTier ? Math.max(0, nextTierMin - demoRepScore) : null,
              progress_to_next: demoProgress
            },
            recent_activity: [],
            last_updated_at: new Date().toISOString()
          };
          updateUI(demoSummary);
          console.log('[Wallet] Using demo state:', demoSummary);
          return;
        }
      }

      // Load from API with cache-busting if forceRefresh is true
      const summary = await apiWalletSummary(forceRefresh);
      console.log('[Wallet] Wallet summary:', summary);
      
      if (summary) {
        updateUI(summary);
        // Cache Nova balance for redeem flow
        if (summary.nova_balance !== undefined) {
          sessionStorage.setItem('nerava_nova_balance', summary.nova_balance.toString());
        }
        // Reset error count on successful fetch
        consecutiveErrors = 0;
        hideRetryBanner();
      }
    } catch (e) {
      console.error('[Wallet] Failed to load wallet summary:', e.message);
      
      // Increment error count (will be handled by pollWalletSummary if called from polling)
      // For direct calls, show error alert
      if (errorAlertEl) {
        errorAlertEl.style.display = 'block';
        errorAlertEl.onclick = () => {
          loadWalletSummary();
        };
      }
      // Re-throw for pollWalletSummary to catch
      throw e;
    }
  };

  // Retry banner functions
  function showRetryBanner() {
    const retryBanner = rootEl.querySelector('#wallet-retry-banner');
    if (retryBanner) {
      retryBanner.style.display = 'block';
      retryBanner.onclick = () => {
        hideRetryBanner();
        consecutiveErrors = 0;
        loadWalletSummary();
        startPolling();
      };
    }
  }

  function hideRetryBanner() {
    const retryBanner = rootEl.querySelector('#wallet-retry-banner');
    if (retryBanner) {
      retryBanner.style.display = 'none';
    }
  }

  // Polling wrapper with error backoff
  async function pollWalletSummary() {
    try {
      // Always force refresh during polling to get latest reputation updates
      await loadWalletSummary(true); // Force refresh to get latest data
      consecutiveErrors = 0;  // Reset on success
      hideRetryBanner();
    } catch (err) {
      consecutiveErrors++;
      console.warn(`[Wallet] Poll failed (${consecutiveErrors}/${MAX_POLL_ERRORS}):`, err.message);
      
      if (consecutiveErrors >= MAX_POLL_ERRORS) {
        stopPolling();
        showRetryBanner();
      }
    }
  }

  // Initial load
  await loadWalletSummary();
  
  // Check if wallet should refresh (e.g., after redemption)
  if (sessionStorage.getItem('nerava_wallet_should_refresh') === 'true') {
    console.log('[Wallet] Refresh flag detected, forcing wallet refresh...');
    sessionStorage.removeItem('nerava_wallet_should_refresh');
    // Force refresh with cache-busting to ensure latest data
    await loadWalletSummary(true);
  }

  // Start countdown timer (update every 60 seconds)
  walletCountdownInterval = setInterval(updateCountdown, 60000);

  // Start polling (every 10 seconds) - only while page is visible
  const startPolling = () => {
    stopPolling();  // Clear any existing
    consecutiveErrors = 0;  // Reset error count
    
    walletPollInterval = setInterval(() => {
      // Only poll if page is visible
      if (document.visibilityState === 'visible') {
        pollWalletSummary();
      }
    }, 10000); // 10 seconds
  };

  const stopPolling = () => {
    if (walletPollInterval) {
      clearInterval(walletPollInterval);
      walletPollInterval = null;
    }
  };

  // Start polling when page becomes visible
  if (document.visibilityState === 'visible') {
    startPolling();
  }

  // Handle visibility changes
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      startPolling();
      // Check if we should force refresh (e.g., after redemption)
      const shouldForceRefresh = sessionStorage.getItem('nerava_wallet_should_refresh') === 'true';
      if (shouldForceRefresh) {
        sessionStorage.removeItem('nerava_wallet_should_refresh');
        consecutiveErrors = 0;  // Reset on manual refresh
        loadWalletSummary(true); // Force refresh with cache-busting
      } else {
        consecutiveErrors = 0;  // Reset on manual refresh
        loadWalletSummary(); // Normal refresh when visible
      }
    } else {
      stopPolling();
    }
  });

  // Listen for wallet invalidation events (e.g., after redemption)
  // This must be set up after loadWalletSummary is defined
  handleWalletInvalidate = () => {
    console.log('[Wallet] Received invalidation event, forcing wallet refresh...');
    sessionStorage.removeItem('nerava_wallet_should_refresh'); // Clear flag when event is received
    loadWalletSummary(true); // Force refresh with cache-busting
  };
  window.addEventListener('nerava:wallet:invalidate', handleWalletInvalidate);
  
  // Also check for refresh flag periodically when page is visible (in case event was missed)
  const checkRefreshFlag = () => {
    if (document.visibilityState === 'visible') {
      const shouldRefresh = sessionStorage.getItem('nerava_wallet_should_refresh') === 'true';
      if (shouldRefresh) {
        console.log('[Wallet] Refresh flag detected on periodic check, forcing refresh...');
        handleWalletInvalidate();
      }
    }
  };
  // Check every 2 seconds when page is visible
  walletRefreshCheckInterval = setInterval(checkRefreshFlag, 2000);
  
  // Enhance cleanup to remove event listener
  const originalCleanup = cleanup;
  cleanup = () => {
    if (handleWalletInvalidate) {
      window.removeEventListener('nerava:wallet:invalidate', handleWalletInvalidate);
    }
    if (originalCleanup) originalCleanup();
  };

  // Wire actions
  rootEl.querySelector('#w-generate-card')?.addEventListener('click', () => {
    console.log('[Wallet] Generate Virtual Card clicked');
    window.location.hash = '#/virtual-card';
  });

  rootEl.querySelector('#w-redeem-btn')?.addEventListener('click', () => {
    console.log('[Wallet] Redeem Nova clicked');
    // Set intent flag for Discover to auto-select merchant
    sessionStorage.setItem('nerava_redeem_intent', 'true');
    setTab('discover');
    // Dispatch event to trigger auto-select in Discover tab
    window.dispatchEvent(new CustomEvent('nerava:discover:redeem_start'));
  });


  // Cleanup on page unmount (when navigating away)
  // Store cleanup function on element for app.js to call if needed
  rootEl._walletCleanup = cleanup;
  
  // Also cleanup when page is hidden/unloaded
  window.addEventListener('beforeunload', cleanup);
  
  // Return cleanup function for explicit cleanup
  return cleanup;
}

// Export stopWalletTimers for external cleanup (e.g., from app.js)
export { stopWalletTimers };
