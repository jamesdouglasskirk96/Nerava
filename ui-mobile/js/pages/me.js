// Me page logic
import { createModal, showModal, trapFocus } from '../components/modal.js';
import { apiGet, apiPost } from '../core/api.js';
window.Nerava = window.Nerava || {};
window.Nerava.pages = window.Nerava.pages || {};

(function(){
  window.initMe = function initMe(){
    // Load lightweight profile stats
    const fs = document.getElementById('followersCount');
    const fg = document.getElementById('followingCount');
    const rep = document.getElementById('repScore');

    // Try hitting social APIs; fallback to zeros
    if (window.Nerava && window.Nerava.core && window.Nerava.core.api) {
      apiGet('/v1/social/followers?user_id=you').then(r => { 
        if (fs) fs.textContent = (r?.length ?? 0); 
      }).catch(()=>{ 
        if (fs) fs.textContent = '0'; 
      });
      
      apiGet('/v1/social/following?user_id=you').then(r => { 
        if (fg) fg.textContent = (r?.length ?? 0); 
      }).catch(()=>{ 
        if (fg) fg.textContent = '0'; 
      });
    } else {
      if (fs) fs.textContent = '0';
      if (fg) fg.textContent = '0';
    }

    // Load EnergyRep score and add details button
    loadEnergyRepScore();
    addEnergyRepDetailsButton();
  };
})();

async function loadEnergyRepScore() {
  const rep = document.getElementById('repScore');
  if (!rep) return;
  
  try {
    const data = await apiGet('/v1/profile/energy_rep?user_id=current_user');
    if (data && data.total_score !== undefined) {
      rep.textContent = data.total_score;
    } else {
      rep.textContent = '—';
    }
  } catch (e) {
    console.error('Failed to load EnergyRep score:', e);
    rep.textContent = '—';
  }
}

function addEnergyRepDetailsButton() {
  const repEl = document.getElementById('repScore');
  if (!repEl) return;
  
  const detailsBtn = document.createElement('button');
  detailsBtn.textContent = 'View details';
  detailsBtn.className = 'btn btn-secondary';
  detailsBtn.style.cssText = 'margin-left: 8px; font-size: 0.875rem;';
  
  detailsBtn.addEventListener('click', async () => {
    try {
      const data = await apiGet('/v1/profile/energy_rep?user_id=current_user');
      const breakdown = data?.breakdown || {};
      
      const content = `
        <div class="energy-rep-breakdown">
          <div class="breakdown-item">
            <span class="label">Charging Score</span>
            <span class="score">${breakdown.charging_score || 0}</span>
            <span class="max">/ 600</span>
          </div>
          <div class="breakdown-item">
            <span class="label">Referrals</span>
            <span class="score">${breakdown.referrals || 0}</span>
            <span class="max">/ 200</span>
          </div>
          <div class="breakdown-item">
            <span class="label">Merchant Redemptions</span>
            <span class="score">${breakdown.merchant || 0}</span>
            <span class="max">/ 150</span>
          </div>
          <div class="breakdown-item">
            <span class="label">V2G Sessions</span>
            <span class="score">${breakdown.v2g || 0}</span>
            <span class="max">/ 250</span>
          </div>
          <div class="breakdown-item" style="border-top: 1px solid #e5e7eb; margin-top: 0.5rem; padding-top: 0.5rem;">
            <span class="label" style="font-weight: 600;">Total Score</span>
            <span class="score" style="font-size: 1.125rem;">${data?.total_score || 0}</span>
            <span class="max">/ 1000</span>
          </div>
        </div>
      `;
      
      const modal = createModal('EnergyRep Breakdown', content);
      showModal(modal);
      // after modal open:
      // trapFocus(modalEl);
    } catch (e) {
      console.error('Failed to load EnergyRep breakdown:', e);
      alert('Failed to load EnergyRep details');
    }
  });
  
  repEl.parentNode.appendChild(detailsBtn);
}

// Export init function
window.Nerava.pages.me = {
  init: window.initMe
};