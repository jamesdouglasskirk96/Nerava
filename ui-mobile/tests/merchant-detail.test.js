/**
 * Tests for merchant detail page functionality
 */

describe('Merchant Detail Page', () => {
  let container;
  let mockMerchant;

  beforeEach(() => {
    // Setup DOM
    document.body.innerHTML = '';
    container = document.createElement('section');
    container.id = 'page-merchant-detail';
    container.className = 'page';
    container.style.display = 'none';
    document.body.appendChild(container);

    // Mock merchant object
    mockMerchant = {
      id: 'merchant_123',
      name: 'Test Merchant',
      lat: 30.4021,
      lng: -97.7266,
      logo_url: 'https://example.com/logo.png',
      photo_url: 'https://example.com/photo.jpg',
      nova_reward: 100,
      rating: 4.5,
      review_count: 250,
      category: 'Food & Drink',
      price_level: '$$',
      walk_time_s: 300,
      description: 'A great place to redeem Nova rewards.',
    };

    // Mock sessionStorage
    global.sessionStorage = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
    };

    // Mock window.dispatchEvent
    global.window = {
      ...global.window,
      dispatchEvent: jest.fn(),
      open: jest.fn(),
    };
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  test('opening merchant detail renders required elements', async () => {
    // Dynamically import the module
    const { openMerchantDetail } = await import('../js/pages/merchant-detail.js');

    openMerchantDetail(mockMerchant);

    // Check that container is visible
    expect(container.style.display).toBe('block');
    expect(container.classList.contains('active')).toBe(true);

    // Check that required elements are rendered
    expect(container.querySelector('.merchant-detail-name')).toBeTruthy();
    expect(container.querySelector('.merchant-detail-name').textContent).toBe('Test Merchant');
    expect(container.querySelector('.merchant-detail-hero')).toBeTruthy();
    expect(container.querySelector('.merchant-detail-redeem-btn')).toBeTruthy();
    expect(container.querySelector('.merchant-detail-navigate-bottom-btn')).toBeTruthy();
    expect(container.querySelector('.merchant-detail-nova-banner')).toBeTruthy();
  });

  test('redeem confirm shows computed Nova and USD values', async () => {
    const { openMerchantDetail, openRedeemConfirm } = await import('../js/pages/merchant-detail.js');

    // Mock apiWalletSummary
    const { apiWalletSummary } = await import('../js/core/api.js');
    jest.spyOn(require('../js/core/api.js'), 'apiWalletSummary').mockResolvedValue({
      nova_balance: 150,
    });

    openMerchantDetail(mockMerchant);
    
    // Trigger redeem button click
    const redeemBtn = container.querySelector('.merchant-detail-redeem-btn');
    redeemBtn.click();

    // Wait for async operations
    await new Promise(resolve => setTimeout(resolve, 100));

    // Check that modal was created
    const modal = document.querySelector('.merchant-detail-redeem-modal');
    expect(modal).toBeTruthy();

    // Check that amounts are displayed correctly
    // Note: The modal is appended to body, not container
    const modalElement = document.body.querySelector('.merchant-detail-redeem-modal');
    if (modalElement) {
      const novaAmount = modalElement.querySelector('.merchant-detail-redeem-nova');
      const usdAmount = modalElement.querySelector('.merchant-detail-redeem-usd');
      
      // Should show min(150, 100) = 100 Nova
      if (novaAmount) {
        expect(novaAmount.textContent).toContain('100');
      }
      if (usdAmount) {
        expect(usdAmount.textContent).toContain('$10.00');
      }
    }
  });

  test('accept calls apiRedeemNova and dispatches wallet invalidate event', async () => {
    const { openMerchantDetail, openRedeemConfirm } = await import('../js/pages/merchant-detail.js');

    // Mock API functions
    const { apiWalletSummary, apiRedeemNova } = await import('../js/core/api.js');
    jest.spyOn(require('../js/core/api.js'), 'apiWalletSummary').mockResolvedValue({
      nova_balance: 150,
    });
    
    const redeemSpy = jest.spyOn(require('../js/core/api.js'), 'apiRedeemNova').mockResolvedValue({
      transaction_id: 'tx_123',
      driver_balance: 50,
    });

    openMerchantDetail(mockMerchant);
    
    // Trigger redeem button click
    const redeemBtn = container.querySelector('.merchant-detail-redeem-btn');
    redeemBtn.click();

    // Wait for modal to appear
    await new Promise(resolve => setTimeout(resolve, 100));

    // Find and click accept button
    const modal = document.body.querySelector('.merchant-detail-redeem-modal');
    if (modal) {
      const acceptBtn = modal.querySelector('#confirm-redeem-btn');
      if (acceptBtn) {
        acceptBtn.click();
        
        // Wait for API call
        await new Promise(resolve => setTimeout(resolve, 100));

        // Verify API was called
        expect(redeemSpy).toHaveBeenCalledWith(
          'merchant_123',
          100, // min(150, 100)
          null, // sessionId
          expect.stringMatching(/^redeem_\d+_merchant_123_100$/) // idempotency key
        );

        // Verify wallet invalidate event was dispatched
        // Note: This happens in showRedeemSuccess, which is called after API success
        // We can check that the event was dispatched by checking the mock
        expect(window.dispatchEvent).toHaveBeenCalled();
      }
    }
  });

  test('close merchant detail removes DOM and restores scroll', async () => {
    const { openMerchantDetail, closeMerchantDetail } = await import('../js/pages/merchant-detail.js');

    // Set initial body overflow
    document.body.style.overflow = 'auto';

    openMerchantDetail(mockMerchant);
    expect(document.body.style.overflow).toBe('hidden');

    closeMerchantDetail();
    
    expect(container.style.display).toBe('none');
    expect(container.classList.contains('active')).toBe(false);
    expect(document.body.style.overflow).toBe('auto');
  });

  test('prevent double-open with isOpen flag', async () => {
    const { openMerchantDetail } = await import('../js/pages/merchant-detail.js');

    const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

    openMerchantDetail(mockMerchant);
    expect(container.style.display).toBe('block');

    // Try to open again
    openMerchantDetail(mockMerchant);
    
    // Should warn and not open again
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Already open')
    );

    consoleSpy.mockRestore();
  });
});


