// Wallet page logic
window.Nerava = window.Nerava || {};
window.Nerava.pages = window.Nerava.pages || {};

function updateWalletProgress() {
  const progressEl = document.getElementById('walletProgress');
  if (progressEl) {
    const progress = progressEl.querySelector('.progress-bar');
    if (progress) {
      progress.style.width = '75%';
    }
  }
}

async function updateCommunityPool() {
  if (!window.Nerava.core.api.canCallApi()) return;
  
  try {
    const pool = await window.Nerava.core.api.apiJson('/v1/social/pool');
    const poolEl = document.getElementById('communityPool');
    if (poolEl) {
      const amount = window.Nerava.core.utils.formatCurrency(pool.total_community_cents);
      poolEl.textContent = `Community shared this month: ${amount}`;
    }
  } catch (e) {
    console.error('Failed to load community pool:', e);
  }
}

function initWallet() {
  updateWalletProgress();
  updateCommunityPool();
}

// Export init function
window.Nerava.pages.wallet = {
  init: initWallet
};
