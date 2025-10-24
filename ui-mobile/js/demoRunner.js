(function(){
  const sleep = ms => new Promise(r=>setTimeout(r, ms));
  const $ = s => document.querySelector(s);

  // Simple caption overlay
  function caption(msg){
    let el = $('#demo-caption');
    if(!el){
      el = document.createElement('div');
      el.id = 'demo-caption';
      el.style.cssText = 'position:fixed;bottom:76px;left:50%;transform:translateX(-50%);background:#0b1220;color:#fff;padding:10px 14px;border-radius:12px;font-weight:600;z-index:99999;box-shadow:0 6px 24px rgba(0,0,0,.25)';
      document.body.appendChild(el);
    }
    el.textContent = msg;
  }
  function highlight(sel){
    const prev = document.querySelector('.demo-highlight');
    if(prev) prev.classList.remove('demo-highlight');
    const el = document.querySelector(sel);
    if(el){ el.classList.add('demo-highlight'); }
  }
  const addStyles = ()=>{
    if(document.getElementById('demo-runner-css')) return;
    const style = document.createElement('style');
    style.id='demo-runner-css';
    style.textContent = `
      .demo-highlight{ outline:3px solid #22c55e; outline-offset:2px; border-radius:10px; transition: outline .2s; }
    `;
    document.head.appendChild(style);
  };

  async function clickTab(tabName){
    const btn = document.querySelector(`.tabbar .tab[data-tab="${tabName}"]`);
    if(btn){ btn.click(); await sleep(450); }
  }

  async function runInvestorScript(){
    addStyles();
    caption('Explore: nearby deals & map'); highlight('#page-explore');
    await clickTab('explore'); await sleep(800);

    caption('Navigate: best hub now'); highlight('#btn-navigate');
    const nav = $('#btn-navigate'); if(nav){ nav.scrollIntoView({behavior:'smooth', block:'center'}); await sleep(300); }
    await sleep(900);

    caption('Wallet: rewards credit in real-time'); highlight('#page-wallet');
    await clickTab('wallet'); await sleep(900);

    caption('Profile: your EnergyRep (portable credential)'); highlight('#page-profile');
    await clickTab('profile'); await sleep(900);
    // If there is a "details" button/modal, try to open it
    const detailsBtn = document.querySelector('[data-energyrep-details]') || document.querySelector('#btn-energyrep-details');
    if(detailsBtn){ detailsBtn.click(); await sleep(900); }

    caption('Dev: Merchant Intel & Behavior Cloud'); highlight('.tabbar');
    // if your router uses hash for dev, navigate there
    if(location.hash !== '#/dev'){ location.hash = '#/dev'; await sleep(900); }

    caption('Demo complete ✨');
    await sleep(1200);
    const cap = document.getElementById('demo-caption'); if(cap){ cap.remove(); }
    const hl = document.querySelector('.demo-highlight'); if(hl){ hl.classList.remove('demo-highlight'); }
  }

  // Expose a single entry on window
  window.NeravaDemoRunner = { runInvestorScript };
})();
