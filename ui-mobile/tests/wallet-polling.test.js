/**
 * Regression tests for wallet polling interval management
 * Ensures no duplicate intervals are created when initWalletPage is called multiple times
 */

describe('Wallet Polling Interval Management (Regression Test)', () => {
  let container;
  let originalSetInterval;
  let originalClearInterval;
  let intervalCallbacks;
  let intervalIds;
  let clearIntervalCalls;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    
    // Track interval calls
    intervalCallbacks = [];
    intervalIds = [];
    clearIntervalCalls = [];
    let nextIntervalId = 1;
    
    // Mock setInterval
    originalSetInterval = window.setInterval;
    window.setInterval = (callback, delay) => {
      const id = nextIntervalId++;
      intervalCallbacks.push({ id, callback, delay });
      intervalIds.push(id);
      return id;
    };
    
    // Mock clearInterval
    originalClearInterval = window.clearInterval;
    window.clearInterval = (id) => {
      clearIntervalCalls.push(id);
      const index = intervalIds.indexOf(id);
      if (index > -1) {
        intervalIds.splice(index, 1);
      }
    };
  });

  afterEach(() => {
    // Restore original functions
    window.setInterval = originalSetInterval;
    window.clearInterval = originalClearInterval;
    
    // Cleanup
    if (container && container.parentNode) {
      document.body.removeChild(container);
    }
    container = null;
    intervalCallbacks = [];
    intervalIds = [];
    clearIntervalCalls = [];
  });

  test('No duplicate intervals when initWalletPage called multiple times', async () => {
    const { initWalletPage, stopWalletTimers } = await import('../js/pages/wallet-new.js');
    
    // Mock apiWalletSummary
    const mockApiWalletSummary = jest.fn().mockResolvedValue({
      nova_balance: 1000,
      nova_balance_cents: 10000,
      conversion_rate_cents: 10,
      usd_equivalent: '$100.00',
      charging_detected: false,
      offpeak_active: false,
      window_ends_in_seconds: 3600,
      reputation: {
        tier: 'Bronze',
        points: 50,
        points_to_next: 50
      },
      recent_activity: [],
      last_updated_at: new Date().toISOString()
    });

    jest.mock('../js/core/api.js', () => ({
      apiWalletSummary: mockApiWalletSummary
    }));
    
    // Call initWalletPage twice rapidly
    await initWalletPage(container);
    await new Promise(resolve => setTimeout(resolve, 10));
    
    // Call again (should cleanup first, then create new intervals)
    await initWalletPage(container);
    await new Promise(resolve => setTimeout(resolve, 10));
    
    // Should have exactly one polling interval (45s) and one countdown interval (60s)
    const pollIntervals = intervalCallbacks.filter(cb => cb.delay === 45000);
    const countdownIntervals = intervalCallbacks.filter(cb => cb.delay === 60000);
    
    expect(pollIntervals.length).toBeLessThanOrEqual(1);
    expect(countdownIntervals.length).toBeLessThanOrEqual(1);
    
    // Verify cleanup was called (clearInterval should have been called)
    expect(clearIntervalCalls.length).toBeGreaterThan(0);
  });

  test('stopWalletTimers clears all intervals', async () => {
    const { initWalletPage, stopWalletTimers } = await import('../js/pages/wallet-new.js');
    
    // Mock apiWalletSummary
    jest.spyOn(await import('../js/core/api.js'), 'apiWalletSummary').mockResolvedValue({
      nova_balance: 1000,
      nova_balance_cents: 10000,
      conversion_rate_cents: 10,
      usd_equivalent: '$100.00',
      charging_detected: false,
      offpeak_active: false,
      window_ends_in_seconds: 3600,
      reputation: {
        tier: 'Bronze',
        points: 50,
        points_to_next: 50
      },
      recent_activity: [],
      last_updated_at: new Date().toISOString()
    });
    
    await initWalletPage(container);
    await new Promise(resolve => setTimeout(resolve, 10));
    
    const intervalsBeforeCleanup = intervalIds.length;
    expect(intervalsBeforeCleanup).toBeGreaterThan(0);
    
    // Call stopWalletTimers
    stopWalletTimers();
    
    // All intervals should be cleared
    expect(clearIntervalCalls.length).toBeGreaterThan(0);
    expect(intervalIds.length).toBe(0);
  });

  test('Cleanup function clears intervals when called', async () => {
    const { initWalletPage } = await import('../js/pages/wallet-new.js');
    
    // Mock apiWalletSummary
    jest.spyOn(await import('../js/core/api.js'), 'apiWalletSummary').mockResolvedValue({
      nova_balance: 1000,
      nova_balance_cents: 10000,
      conversion_rate_cents: 10,
      usd_equivalent: '$100.00',
      charging_detected: false,
      offpeak_active: false,
      window_ends_in_seconds: 3600,
      reputation: {
        tier: 'Bronze',
        points: 50,
        points_to_next: 50
      },
      recent_activity: [],
      last_updated_at: new Date().toISOString()
    });
    
    const cleanup = await initWalletPage(container);
    await new Promise(resolve => setTimeout(resolve, 10));
    
    expect(intervalIds.length).toBeGreaterThan(0);
    
    // Call cleanup function
    cleanup();
    
    // Intervals should be cleared
    expect(clearIntervalCalls.length).toBeGreaterThan(0);
    expect(intervalIds.length).toBe(0);
  });
});






