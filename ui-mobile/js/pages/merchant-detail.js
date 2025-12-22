/**
 * Merchant Detail Page - Resy-style full-page merchant detail screen
 * 
 * Provides a full-screen merchant detail view with hero image, merchant info,
 * and redeem flow integration.
 */

import { apiRedeemNova, apiWalletSummary } from '../core/api.js';
import { setTab } from '../app.js';
import { createModal, showModal } from '../components/modal.js';

// Module-scoped state
let currentMerchant = null;
let isOpen = false;
let listeners = [];
let cleanupFunctions = [];
let originalBodyOverflow = '';

// Toast helper
function showToast(message) {
  const toast = document.createElement('div');
  toast.style.cssText = 'position:fixed;left:50%;bottom:100px;transform:translateX(-50%);background:#111;color:#fff;padding:10px 14px;border-radius:12px;z-index:99999;font-weight:700;font-size:14px';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/**
 * Open merchant detail page
 * @param {Object} merchant - Merchant object with id, name, lat, lng, etc.
 */
export function openMerchantDetail(merchant) {
  if (isOpen) {
    console.warn('[MerchantDetail] Already open, ignoring');
    return;
  }

  if (!merchant || !merchant.id) {
    console.error('[MerchantDetail] Invalid merchant object:', merchant);
    showToast('Invalid merchant data');
    return;
  }

  currentMerchant = merchant;
  isOpen = true;

  // Prevent background scroll
  originalBodyOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';

  const container = document.getElementById('page-merchant-detail');
  if (!container) {
    console.error('[MerchantDetail] Container not found');
    return;
  }

  // Normalize merchant data with defaults
  const merchantData = {
    id: merchant.id,
    name: merchant.name || 'Merchant',
    lat: merchant.lat || merchant.latitude || null,
    lng: merchant.lng || merchant.longitude || null,
    logo_url: merchant.logo_url || merchant.logo || null,
    photo_url: merchant.photo_url || merchant.image_url || null,
    nova_reward: merchant.nova_reward || merchant.nova || 0,
    rating: merchant.rating || 4.6,
    review_count: merchant.review_count || merchant.rating_count || 0,
    category: merchant.category || 'Other',
    price_level: merchant.price_level || merchant.price_tier || '$$',
    walk_time_s: merchant.walk_time_s || 0,
    description: merchant.description || merchant.why_we_like_it || 'NYC-style breakfast sandwiches',
  };

  // Calculate USD value (assuming 10 cents per Nova)
  const conversionRate = 10; // cents per Nova
  const usdValue = ((merchantData.nova_reward * conversionRate) / 100).toFixed(2);

  // Helper to ensure asset paths have /app prefix
  const normalizeAssetPath = (path) => {
    if (!path) return null;
    // If it's already a full URL, return as-is
    if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('data:')) {
      return path;
    }
    // If it starts with /app, return as-is
    if (path.startsWith('/app/')) {
      return path;
    }
    // If it starts with /, add /app prefix
    if (path.startsWith('/')) {
      return '/app' + path;
    }
    // Otherwise, assume it's relative and add /app/assets/
    return '/app/assets/' + path;
  };

  // Hero image (use photo_url, logo_url, or placeholder)
  const heroImage = normalizeAssetPath(merchantData.photo_url || merchantData.logo_url) || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiM5Y2EzYWYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';

  // Logo for overlay badge
  // If logo_url points to a hero image (contains 'hero'), try to use the logo version instead
  let logoImage = merchantData.logo_url;
  if (logoImage && logoImage.includes('hero')) {
    // Replace 'hero' with 'logo' in the path to get the actual logo
    logoImage = logoImage.replace('hero', 'logo');
  }
  // If no logo_url or it's the same as hero, try photo_url (but only if different)
  if (!logoImage || logoImage === heroImage) {
    logoImage = merchantData.photo_url && merchantData.photo_url !== heroImage ? merchantData.photo_url : null;
  }
  // Normalize the logo path to include /app prefix
  logoImage = normalizeAssetPath(logoImage);

  // Distance to charger text
  const distanceToChargerText = merchantData.walk_time_s > 0
    ? `${Math.max(1, Math.round(merchantData.walk_time_s / 60))} min walk to charger`
    : merchantData.distance_text || 'Near charger';

  // Format hours of operation - show only current status and next open time
  function formatHours(merchant) {
    // Check if hours data exists
    if (merchant.opening_hours && merchant.opening_hours.length > 0) {
      // Calculate current status from structured hours
      const now = new Date();
      const currentDay = now.getDay(); // 0 = Sunday, 1 = Monday, etc.
      const currentHour = now.getHours();
      const currentMinute = now.getMinutes();
      const currentTime = currentHour * 60 + currentMinute;
      
      // Find today's hours
      const todayIndex = currentDay === 0 ? 6 : currentDay - 1; // Convert to Mon=0, Sun=6
      const todayHours = merchant.opening_hours[todayIndex];
      
      let isOpen = false;
      let nextOpen = null;
      
      if (todayHours && todayHours.open && todayHours.close) {
        const openTime = parseTime(todayHours.open);
        const closeTime = parseTime(todayHours.close);
        isOpen = currentTime >= openTime && currentTime < closeTime;
        
        if (!isOpen && currentTime < openTime) {
          nextOpen = formatTime(todayHours.open);
        } else if (!isOpen) {
          // Find next day's open time
          for (let i = 1; i <= 7; i++) {
            const nextDayIndex = (todayIndex + i) % 7;
            const nextDayHours = merchant.opening_hours[nextDayIndex];
            if (nextDayHours && nextDayHours.open) {
              const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
              nextOpen = `${formatTime(nextDayHours.open)} ${dayNames[nextDayIndex]}`;
              break;
            }
          }
        }
      }
      
      const status = isOpen ? 'Open' : 'Closed';
      return `
        <div class="merchant-detail-hours-status">
          <span class="merchant-detail-hours-status-text ${isOpen ? 'open' : 'closed'}">${status}</span>
          ${nextOpen ? `<span class="merchant-detail-hours-next">Opens ${nextOpen}</span>` : ''}
        </div>
      `;
    } else if (merchant.hours) {
      // Simple string format - try to extract status
      return `<div class="merchant-detail-hours-text">${merchant.hours}</div>`;
    } else {
      // Default hours for demo
      const now = new Date();
      const currentHour = now.getHours();
      const isOpen = currentHour >= 7 && currentHour < 22;
      const status = isOpen ? 'Open' : 'Closed';
      const nextOpen = isOpen ? null : '7 AM';
      
      return `
        <div class="merchant-detail-hours-status">
          <span class="merchant-detail-hours-status-text ${isOpen ? 'open' : 'closed'}">${status}</span>
          ${nextOpen ? `<span class="merchant-detail-hours-next">Opens ${nextOpen}</span>` : ''}
        </div>
      `;
    }
  }

  function parseTime(timeString) {
    // Parse time string to minutes since midnight
    if (!timeString) return 0;
    const match = timeString.match(/(\d{1,2}):?(\d{2})?/);
    if (match) {
      const hours = parseInt(match[1], 10);
      const minutes = match[2] ? parseInt(match[2], 10) : 0;
      return hours * 60 + minutes;
    }
    return 0;
  }

  function formatTime(timeString) {
    // Handle various time formats
    if (!timeString) return '';
    if (typeof timeString === 'string') {
      // Try to parse "HH:MM" or "HHMM" format
      const match = timeString.match(/(\d{1,2}):?(\d{2})?/);
      if (match) {
        let hours = parseInt(match[1], 10);
        const minutes = match[2] ? parseInt(match[2], 10) : 0;
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12 || 12;
        return `${hours}:${minutes.toString().padStart(2, '0')} ${ampm}`;
      }
      return timeString;
    }
    return timeString.toString();
  }

  // Render page
  container.innerHTML = `
    <div class="merchant-detail-page">
      <!-- Hero Section -->
      <div class="merchant-detail-hero">
        <img src="${heroImage}" alt="${merchantData.name}" class="merchant-detail-hero-image" />
        <div class="merchant-detail-hero-overlay"></div>
        
        <!-- Logo Badge Overlay -->
        ${logoImage ? `
          <div class="merchant-detail-hero-logo-badge">
            <img src="${logoImage}" alt="${merchantData.name}" class="merchant-detail-hero-logo" onerror="this.parentElement.style.display='none'" />
          </div>
        ` : ''}
        
        <!-- Overlay Controls -->
        <div class="merchant-detail-hero-controls">
          <button class="merchant-detail-close-btn" id="merchant-detail-close" aria-label="Close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
          <div class="merchant-detail-action-buttons">
            <button class="merchant-detail-like-btn" id="merchant-detail-like" aria-label="Like">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
            </button>
            <button class="merchant-detail-share-btn" id="merchant-detail-share" aria-label="Share">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="18" cy="5" r="3"/>
                <circle cx="6" cy="12" r="3"/>
                <circle cx="18" cy="19" r="3"/>
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Content Section -->
      <div class="merchant-detail-content">
        <!-- Merchant Name -->
        <h1 class="merchant-detail-name">${merchantData.name}</h1>

        <!-- Description -->
        ${merchantData.description ? `
          <div class="merchant-detail-description-text">
            ${merchantData.description}
          </div>
        ` : ''}

        <!-- Meta Info -->
        <div class="merchant-detail-meta">
          <span class="merchant-detail-rating">★ ${merchantData.rating.toFixed(1)}</span>
          <span class="merchant-detail-rating-count">(${merchantData.review_count.toLocaleString()})</span>
          <span class="merchant-detail-dot">•</span>
          <span class="merchant-detail-category">${merchantData.category}</span>
          <span class="merchant-detail-dot">•</span>
          <span class="merchant-detail-price">${merchantData.price_level}</span>
          <span class="merchant-detail-dot">•</span>
          <span class="merchant-detail-location">
            <svg class="merchant-detail-location-icon" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>
            ${distanceToChargerText}
          </span>
        </div>

        <!-- Hours of Operation -->
        <div class="merchant-detail-description">
          <div class="merchant-detail-hours">
            ${formatHours(merchantData)}
          </div>
        </div>

        <!-- Nova Accepted Banner -->
        <div class="merchant-detail-nova-banner">
          <div class="merchant-detail-nova-banner-icon">⚡</div>
          <div class="merchant-detail-nova-banner-text">
            <div class="merchant-detail-nova-banner-title">Nova accepted here</div>
            <div class="merchant-detail-nova-banner-subtitle">Redeem up to ${merchantData.nova_reward} Nova ($${usdValue})</div>
          </div>
        </div>
      </div>

      <!-- Sticky Bottom CTA -->
      <div class="merchant-detail-cta">
        <button class="merchant-detail-redeem-btn" id="merchant-detail-redeem">
          Redeem Nova
        </button>
        <button class="merchant-detail-navigate-bottom-btn" id="merchant-detail-navigate-bottom">
          Navigate
        </button>
      </div>
    </div>
  `;

  // Helper functions for like functionality
  const getLikedMerchants = () => {
    try {
      const liked = localStorage.getItem('nerava_liked_merchants');
      return liked ? JSON.parse(liked) : [];
    } catch (e) {
      return [];
    }
  };

  const isMerchantLiked = (merchantId) => {
    return getLikedMerchants().includes(merchantId);
  };

  const toggleMerchantLike = (merchantId) => {
    const liked = getLikedMerchants();
    const index = liked.indexOf(merchantId);
    if (index > -1) {
      liked.splice(index, 1);
      return false; // Unliked
    } else {
      liked.push(merchantId);
      return true; // Liked
    }
  };

  const saveLikedMerchants = (liked) => {
    try {
      localStorage.setItem('nerava_liked_merchants', JSON.stringify(liked));
    } catch (e) {
      console.error('Failed to save liked merchants:', e);
    }
  };

  // Wire event listeners
  const closeBtn = container.querySelector('#merchant-detail-close');
  const likeBtn = container.querySelector('#merchant-detail-like');
  const shareBtn = container.querySelector('#merchant-detail-share');
  const navigateBottomBtn = container.querySelector('#merchant-detail-navigate-bottom');
  const redeemBtn = container.querySelector('#merchant-detail-redeem');

  // Initialize like button state
  const merchantId = merchantData.id;
  const isLiked = isMerchantLiked(merchantId);
  if (likeBtn) {
    if (isLiked) {
      likeBtn.classList.add('liked');
      likeBtn.querySelector('svg').style.fill = 'currentColor';
    }
  }

  const handleClose = () => closeMerchantDetail();
  const handleLike = () => {
    const wasLiked = toggleMerchantLike(merchantId);
    const liked = getLikedMerchants();
    saveLikedMerchants(liked);
    
    if (likeBtn) {
      const svg = likeBtn.querySelector('svg');
      if (wasLiked) {
        likeBtn.classList.add('liked');
        if (svg) svg.style.fill = 'currentColor';
        showToast('Added to favorites');
      } else {
        likeBtn.classList.remove('liked');
        if (svg) svg.style.fill = 'none';
        showToast('Removed from favorites');
      }
    }
  };
  const handleShare = async () => {
    try {
      const shareData = {
        title: merchantData.name,
        text: `Check out ${merchantData.name}! Redeem up to ${merchantData.nova_reward} Nova ($${usdValue}) here.`,
        url: window.location.href
      };

      // Try Web Share API first (mobile browsers)
      if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
        await navigator.share(shareData);
        showToast('Shared successfully!');
      } else {
        // Fallback: Copy to clipboard
        const shareText = `${merchantData.name}\nRedeem up to ${merchantData.nova_reward} Nova ($${usdValue})\n${window.location.href}`;
        await navigator.clipboard.writeText(shareText);
        showToast('Link copied to clipboard!');
      }
    } catch (error) {
      // User cancelled or error occurred
      if (error.name !== 'AbortError') {
        console.error('Share failed:', error);
        // Fallback to clipboard
        try {
          const shareText = `${merchantData.name}\nRedeem up to ${merchantData.nova_reward} Nova ($${usdValue})\n${window.location.href}`;
          await navigator.clipboard.writeText(shareText);
          showToast('Link copied to clipboard!');
        } catch (clipboardError) {
          showToast('Unable to share');
        }
      }
    }
  };
  const handleNavigate = () => {
    if (merchantData.lat && merchantData.lng) {
      const mapsUrl = `https://maps.apple.com/?daddr=${merchantData.lat},${merchantData.lng}`;
      window.open(mapsUrl, '_blank');
    } else {
      showToast('Location not available');
    }
  };
  const handleRedeem = () => openRedeemConfirm(merchantData);

  if (closeBtn) {
    closeBtn.addEventListener('click', handleClose);
    listeners.push({ element: closeBtn, event: 'click', handler: handleClose });
  }

  if (likeBtn) {
    likeBtn.addEventListener('click', handleLike);
    listeners.push({ element: likeBtn, event: 'click', handler: handleLike });
  }

  if (shareBtn) {
    shareBtn.addEventListener('click', handleShare);
    listeners.push({ element: shareBtn, event: 'click', handler: handleShare });
  }

  if (navigateBottomBtn) {
    navigateBottomBtn.addEventListener('click', handleNavigate);
    listeners.push({ element: navigateBottomBtn, event: 'click', handler: handleNavigate });
  }

  if (redeemBtn) {
    redeemBtn.addEventListener('click', handleRedeem);
    listeners.push({ element: redeemBtn, event: 'click', handler: handleRedeem });
  }

  // Handle ESC key
  const handleEsc = (e) => {
    if (e.key === 'Escape' && isOpen) {
      closeMerchantDetail();
    }
  };
  document.addEventListener('keydown', handleEsc);
  listeners.push({ element: document, event: 'keydown', handler: handleEsc });

  // Hide explore page to prevent map from showing through
  const explorePage = document.getElementById('page-explore');
  if (explorePage) {
    explorePage.style.display = 'none';
    explorePage.style.visibility = 'hidden';
  }

  // Show container
  container.style.display = 'block';
  container.classList.add('active');

  // Scroll to top
  container.scrollTop = 0;
}

/**
 * Close merchant detail page
 */
export function closeMerchantDetail() {
  if (!isOpen) return;

  isOpen = false;
  currentMerchant = null;

  // Remove all event listeners
  listeners.forEach(({ element, event, handler }) => {
    element.removeEventListener(event, handler);
  });
  listeners = [];

  // Clear cleanup functions
  cleanupFunctions.forEach((cleanup) => {
    if (typeof cleanup === 'function') {
      cleanup();
    } else if (typeof cleanup === 'number') {
      clearTimeout(cleanup);
    }
  });
  cleanupFunctions = [];

  // Restore explore page visibility
  const explorePage = document.getElementById('page-explore');
  if (explorePage) {
    explorePage.style.display = '';
    explorePage.style.visibility = '';
  }

  // Restore body scroll
  document.body.style.overflow = originalBodyOverflow;

  // Hide container
  const container = document.getElementById('page-merchant-detail');
  if (container) {
    container.style.display = 'none';
    container.classList.remove('active');
    container.innerHTML = '';
  }
}

/**
 * Open redeem confirmation bottom sheet
 * @param {Object} merchant - Merchant object
 */
export async function openRedeemConfirm(merchant) {
  if (!merchant || !merchant.id) {
    showToast('Invalid merchant');
    return;
  }

  // Get current wallet balance
  let novaBalance = 0;
  try {
    const summary = await apiWalletSummary();
    novaBalance = summary.nova_balance || 0;
    sessionStorage.setItem('nerava_nova_balance', novaBalance.toString());
  } catch (e) {
    console.error('[MerchantDetail] Failed to get balance:', e);
    // Try to get from sessionStorage
    const cached = sessionStorage.getItem('nerava_nova_balance');
    if (cached) {
      novaBalance = parseInt(cached, 10);
    } else {
      showToast('Unable to load balance');
      return;
    }
  }

  // Calculate redeem amount
  const maxRedeem = merchant.nova_reward || 0;
  const novaToRedeem = Math.min(novaBalance, maxRedeem);
  const conversionRate = 10; // cents per Nova
  const usdValue = ((novaToRedeem * conversionRate) / 100).toFixed(2);

  if (novaToRedeem <= 0) {
    showToast('No Nova available to redeem');
    return;
  }

  // Create bottom sheet modal
  const modal = document.createElement('div');
  modal.className = 'merchant-detail-redeem-modal';
  modal.id = 'redeem-confirm-modal';
  modal.innerHTML = `
    <div class="merchant-detail-redeem-backdrop" id="redeem-backdrop"></div>
    <div class="merchant-detail-redeem-sheet">
      <div class="merchant-detail-redeem-sheet-handle"></div>
      <div class="merchant-detail-redeem-content">
        <div class="merchant-detail-redeem-header">
          <img src="${merchant.logo_url || merchant.photo_url || ''}" alt="${merchant.name}" class="merchant-detail-redeem-logo" onerror="this.style.display='none'" />
          <h3 class="merchant-detail-redeem-merchant-name">${merchant.name}</h3>
        </div>

        <div class="merchant-detail-redeem-amounts">
          <div class="merchant-detail-redeem-label">You are redeeming</div>
          <div class="merchant-detail-redeem-nova">${novaToRedeem} Nova</div>
          <div class="merchant-detail-redeem-usd">You get $${usdValue} discount</div>
        </div>

        <div class="merchant-detail-redeem-note">
          Show the confirmation screen to the merchant
        </div>

        <button class="merchant-detail-redeem-accept-btn" id="confirm-redeem-btn">
          Accept
        </button>
        <button class="merchant-detail-redeem-cancel-btn" id="cancel-redeem-btn">
          Cancel
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Animate in
  setTimeout(() => {
    modal.classList.add('active');
  }, 10);

  // Wire buttons
  const acceptBtn = modal.querySelector('#confirm-redeem-btn');
  const cancelBtn = modal.querySelector('#cancel-redeem-btn');
  const backdrop = modal.querySelector('#redeem-backdrop');

  const handleAccept = async () => {
    acceptBtn.disabled = true;
    acceptBtn.textContent = 'Processing...';

    try {
      // Generate idempotency key
      const idempotencyKey = `redeem_${Date.now()}_${merchant.id}_${novaToRedeem}`;

      // Call redeem API
      const result = await apiRedeemNova(merchant.id, novaToRedeem, null, idempotencyKey);

      // Dispatch wallet invalidation event to trigger immediate refresh
      window.dispatchEvent(new CustomEvent('nerava:wallet:invalidate'));
      sessionStorage.setItem('nerava_wallet_should_refresh', 'true');

      // Close modal
      modal.classList.remove('active');
      setTimeout(() => {
        modal.remove();
      }, 300);

      // Show success screen
      showRedeemSuccess(merchant, novaToRedeem, result);
    } catch (error) {
      console.error('[MerchantDetail] Redemption failed:', error);
      acceptBtn.disabled = false;
      acceptBtn.textContent = 'Accept';
      showToast('Redemption failed: ' + (error.message || 'Unknown error'));
    }
  };

  const handleCancel = () => {
    modal.classList.remove('active');
    setTimeout(() => {
      modal.remove();
    }, 300);
  };

  if (acceptBtn) {
    acceptBtn.addEventListener('click', handleAccept);
    listeners.push({ element: acceptBtn, event: 'click', handler: handleAccept });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener('click', handleCancel);
    listeners.push({ element: cancelBtn, event: 'click', handler: handleCancel });
  }

  if (backdrop) {
    backdrop.addEventListener('click', handleCancel);
    listeners.push({ element: backdrop, event: 'click', handler: handleCancel });
  }
}

/**
 * Show redemption success screen
 * @param {Object} merchant - Merchant object
 * @param {number} amountNova - Amount of Nova redeemed
 * @param {Object} result - API result with transaction_id, driver_balance, etc.
 */
export function showRedeemSuccess(merchant, amountNova, result) {
  // Close merchant detail page first
  closeMerchantDetail();

  // Create success screen
  const successModal = document.createElement('div');
  successModal.className = 'merchant-detail-success-modal';
  successModal.id = 'redeem-success-modal';
  
  const conversionRate = 10; // cents per Nova
  const usdValue = ((amountNova * conversionRate) / 100).toFixed(2);
  const transactionId = result.transaction_id || result.id || 'N/A';
  const timestamp = new Date().toLocaleString();

  successModal.innerHTML = `
    <div class="merchant-detail-success-backdrop"></div>
    <div class="merchant-detail-success-content">
      <div class="merchant-detail-success-icon">✓</div>
      <h2 class="merchant-detail-success-title">Redemption Successful</h2>
      
      <div class="merchant-detail-success-merchant">${merchant.name}</div>
      
      <div class="merchant-detail-success-amounts">
        <div class="merchant-detail-success-nova">${amountNova} Nova</div>
        <div class="merchant-detail-success-usd">$${usdValue} discount</div>
      </div>

      <div class="merchant-detail-success-details">
        <div class="merchant-detail-success-detail-row">
          <span>Confirmation Code</span>
          <span class="merchant-detail-success-code">${transactionId}</span>
        </div>
        <div class="merchant-detail-success-detail-row">
          <span>Time</span>
          <span>${timestamp}</span>
        </div>
      </div>

      <button class="merchant-detail-success-wallet-btn" id="success-view-wallet">
        View Wallet
      </button>
    </div>
  `;

  document.body.appendChild(successModal);

  // Animate in
  setTimeout(() => {
    successModal.classList.add('active');
  }, 10);

  // Wire button
  const walletBtn = successModal.querySelector('#success-view-wallet');
  const handleViewWallet = async () => {
    successModal.classList.remove('active');
    setTimeout(() => {
      successModal.remove();
    }, 300);

    // Ensure confirmation modal is closed
    const confirmModal = document.getElementById('redeem-confirm-modal');
    if (confirmModal) {
      confirmModal.classList.remove('active');
      setTimeout(() => {
        confirmModal.remove();
      }, 300);
    }

    // Ensure merchant detail page is closed
    closeMerchantDetail();

    // Set flag to indicate wallet should refresh (in case event is missed)
    sessionStorage.setItem('nerava_wallet_should_refresh', 'true');

    // Wait a moment to ensure DB ledger processing is complete
    // The redemption API call is synchronous, but we add a small delay
    // to ensure any async DB commits/processing are finished
    await new Promise(resolve => setTimeout(resolve, 500));

    // Switch to wallet tab
    await setTab('wallet');

    // Wait for wallet page to be initialized, then refresh
    const refreshWallet = async () => {
      const walletEl = document.getElementById('page-wallet');
      if (walletEl && walletEl.dataset.initialized === 'true') {
        // Wallet is initialized, dispatch refresh event after DB processing delay
        // Additional delay ensures DB ledger update is fully committed
        setTimeout(() => {
          console.log('[MerchantDetail] Triggering wallet refresh after DB processing delay');
          window.dispatchEvent(new CustomEvent('nerava:wallet:invalidate'));
          sessionStorage.removeItem('nerava_wallet_should_refresh');
        }, 300);
      } else {
        // Wait a bit more and try again
        setTimeout(refreshWallet, 50);
      }
    };
    
    // Start refresh attempt
    refreshWallet();
    
    // Also dispatch event after additional delay as fallback to ensure DB is processed
    setTimeout(() => {
      console.log('[MerchantDetail] Fallback wallet refresh after DB processing');
      window.dispatchEvent(new CustomEvent('nerava:wallet:invalidate'));
      sessionStorage.removeItem('nerava_wallet_should_refresh');
    }, 800);
  };

  if (walletBtn) {
    walletBtn.addEventListener('click', handleViewWallet);
    listeners.push({ element: walletBtn, event: 'click', handler: handleViewWallet });
  }
}

