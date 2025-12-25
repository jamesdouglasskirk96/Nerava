/**
 * Discover Page - List of Nova-accepting merchants
 * 
 * Shows a focused list of nearby merchants that accept Nova, sorted by distance.
 * No map - just a clean list view for the Austin pilot.
 */

import { apiNovaMerchantsNearby, trackEvent } from '../core/api.js';
import { openMerchantDetail } from './merchant-detail.js';

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

// Module state
let _merchants = [];
let _userLocation = null;
let _isInitialized = false;

// Default location (Austin Domain area)
const DEFAULT_LAT = 30.4021;
const DEFAULT_LNG = -97.7266;
const DEFAULT_RADIUS_M = 2000;

/**
 * Initialize Discover page
 */
export async function initDiscover() {
  if (_isInitialized) {
    console.log('[Discover] Already initialized');
    return;
  }

  const container = $('#page-discover');
  if (!container) {
    console.error('[Discover] Container not found');
    return;
  }

  _isInitialized = true;
  console.log('[Discover] Initializing...');

  // Track page open
  await trackEvent('discover_opened');

  // Request location
  await requestLocation();

  // Load merchants
  await loadNovaMerchants();
}

/**
 * Request user location
 */
async function requestLocation() {
  if (!navigator.geolocation) {
    console.warn('[Discover] Geolocation not available');
    return;
  }

  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        _userLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        console.log('[Discover] Got user location:', _userLocation);
        resolve();
      },
      (error) => {
        console.warn('[Discover] Location permission denied/unavailable:', error.message);
        // Continue without location - will show featured merchants
        resolve();
      },
      {
        timeout: 5000,
        enableHighAccuracy: false
      }
    );
  });
}

/**
 * Load Nova-accepting merchants
 */
async function loadNovaMerchants() {
  const loadingEl = $('#discover-loading');
  const listEl = $('#discover-merchants-list');
  const emptyEl = $('#discover-empty-state');

  // Show loading
  if (loadingEl) loadingEl.style.display = 'block';
  if (listEl) listEl.innerHTML = '';
  if (emptyEl) emptyEl.style.display = 'none';

  try {
    const params = {
      radiusM: DEFAULT_RADIUS_M
    };

    // Add location if available
    if (_userLocation?.lat && _userLocation?.lng) {
      params.lat = _userLocation.lat;
      params.lng = _userLocation.lng;
    }

    console.log('[Discover] Fetching Nova merchants:', params);
    const merchants = await apiNovaMerchantsNearby(params);
    console.log('[Discover] Got merchants:', merchants.length);

    _merchants = merchants || [];

    // Hide loading
    if (loadingEl) loadingEl.style.display = 'none';

    // Render merchants or empty state
    if (_merchants.length > 0) {
      renderMerchantList(_merchants);
      if (emptyEl) emptyEl.style.display = 'none';
    } else {
      renderEmptyState();
      if (listEl) listEl.innerHTML = '';
    }
  } catch (error) {
    console.error('[Discover] Failed to load merchants:', error);
    if (loadingEl) loadingEl.style.display = 'none';
    renderEmptyState();
    if (listEl) listEl.innerHTML = '';
  }
}

/**
 * Render merchant list
 */
function renderMerchantList(merchants) {
  const listEl = $('#discover-merchants-list');
  if (!listEl) return;

  listEl.innerHTML = '';

  merchants.forEach((merchant) => {
    const card = createMerchantCard(merchant);
    if (card) {
      listEl.appendChild(card);
    }
  });
}

/**
 * Create merchant card element
 */
function createMerchantCard(merchant) {
  const card = document.createElement('div');
  card.className = 'merchant-card';
  card.dataset.merchantId = merchant.id;

  // Format distance
  let distanceText = '';
  if (merchant.distance_m !== null && merchant.distance_m !== undefined) {
    const distanceMi = (merchant.distance_m / 1609.34).toFixed(1);
    distanceText = `${distanceMi} mi`;
  }

  // Build card HTML
  card.innerHTML = `
    <div class="merchant-card-content">
      <div class="merchant-card-main">
        <div class="merchant-card-header">
          <h3 class="merchant-card-name">${escapeHtml(merchant.name)}</h3>
          <span class="merchant-card-badge">Nova accepted</span>
        </div>
        <p class="merchant-card-category">${escapeHtml(merchant.category)}</p>
        <p class="merchant-card-offer">${escapeHtml(merchant.offer_headline)}</p>
        ${distanceText ? `<p class="merchant-card-distance">${distanceText}</p>` : ''}
      </div>
      <button class="merchant-card-cta" data-action="use-nova">Use Nova</button>
    </div>
  `;

  // Add click handlers
  const useNovaBtn = card.querySelector('[data-action="use-nova"]');
  if (useNovaBtn) {
    useNovaBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      handleUseNova(merchant);
    });
  }

  // Card click opens merchant detail
  card.addEventListener('click', (e) => {
    // Don't trigger if clicking the CTA button
    if (e.target.closest('[data-action="use-nova"]')) {
      return;
    }
    handleMerchantSelect(merchant);
  });

  return card;
}

/**
 * Handle merchant card selection
 */
async function handleMerchantSelect(merchant) {
  console.log('[Discover] Merchant selected:', merchant.id);
  
  // Track event
  await trackEvent('merchant_selected', { merchant_id: merchant.id });

  // Open merchant detail
  openMerchantDetail(merchant);
}

/**
 * Handle "Use Nova" CTA
 */
async function handleUseNova(merchant) {
  console.log('[Discover] Use Nova tapped:', merchant.id);
  
  // Track event
  await trackEvent('redeem_cta_tapped', { merchant_id: merchant.id });

  // If redemption method is CODE, show code modal
  if (merchant.nova_redemption_method === 'CODE' && merchant.static_discount_code) {
    showCodeModal(merchant);
  } else {
    // Otherwise, open merchant detail
    openMerchantDetail(merchant);
  }
}

/**
 * Show discount code modal
 */
function showCodeModal(merchant) {
  // Create modal
  const modal = document.createElement('div');
  modal.className = 'discover-code-modal';
  modal.innerHTML = `
    <div class="discover-code-backdrop"></div>
    <div class="discover-code-sheet">
      <div class="discover-code-header">
        <h3>${escapeHtml(merchant.name)}</h3>
        <button class="discover-code-close" aria-label="Close">×</button>
      </div>
      <div class="discover-code-content">
        <p class="discover-code-instructions">Show this code to the cashier:</p>
        <div class="discover-code-display">${escapeHtml(merchant.static_discount_code)}</div>
        <p class="discover-code-offer">${escapeHtml(merchant.offer_headline)}</p>
        ${merchant.offer_details ? `<p class="discover-code-details">${escapeHtml(merchant.offer_details)}</p>` : ''}
      </div>
      <div class="discover-code-actions">
        <button class="discover-code-wallet-btn" data-action="wallet-pass">Show Wallet Pass</button>
        <button class="discover-code-close-btn" data-action="close">Close</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // Animate in
  setTimeout(() => {
    modal.classList.add('active');
  }, 10);

  // Wire handlers
  const closeBtn = modal.querySelector('.discover-code-close');
  const closeBtn2 = modal.querySelector('[data-action="close"]');
  const walletBtn = modal.querySelector('[data-action="wallet-pass"]');
  const backdrop = modal.querySelector('.discover-code-backdrop');

  const closeModal = () => {
    modal.classList.remove('active');
    setTimeout(() => {
      modal.remove();
    }, 300);
  };

  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (closeBtn2) closeBtn2.addEventListener('click', closeModal);
  if (backdrop) backdrop.addEventListener('click', closeModal);

  if (walletBtn) {
    walletBtn.addEventListener('click', () => {
      closeModal();
      // Navigate to wallet pass screen
      window.dispatchEvent(new CustomEvent('nerava:navigate', { detail: { tab: 'wallet', page: 'pass' } }));
    });
  }
}

/**
 * Render empty state
 */
function renderEmptyState() {
  const emptyEl = $('#discover-empty-state');
  if (emptyEl) {
    emptyEl.style.display = 'block';
  }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

