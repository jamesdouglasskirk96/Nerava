// Me page logic
window.Nerava = window.Nerava || {};
window.Nerava.pages = window.Nerava.pages || {};

(function(){
  window.initMe = function initMe(){
    // Load lightweight profile stats
    const fs = document.getElementById('followersCount');
    const fg = document.getElementById('followingCount');
    const rep = document.getElementById('repScore');

    // Try hitting social APIs; fallback to zeros
    if (window.Nerava && window.Nerava.core && window.Nerava.core.api && window.Nerava.core.api.apiJson) {
      window.Nerava.core.api.apiJson('/v1/social/followers?user_id=you').then(r => { 
        if (fs) fs.textContent = (r?.length ?? 0); 
      }).catch(()=>{ 
        if (fs) fs.textContent = '0'; 
      });
      
      window.Nerava.core.api.apiJson('/v1/social/following?user_id=you').then(r => { 
        if (fg) fg.textContent = (r?.length ?? 0); 
      }).catch(()=>{ 
        if (fg) fg.textContent = '0'; 
      });
    } else {
      if (fs) fs.textContent = '0';
      if (fg) fg.textContent = '0';
    }

    // Simple local rep score placeholder (can be backed by backend later)
    if (rep) {
      rep.textContent = localStorage.getItem('nerava_rep') ?? '—';
    }
  };
})();

// Export init function
window.Nerava.pages.me = {
  init: window.initMe
};