;(function(){
  const Animations = {};

  // Banner text change transition
  Animations.bannerTransition = function(bannerEl){
    if (!bannerEl) return;
    bannerEl.style.transition = 'transform 180ms ease, opacity 180ms ease';
    bannerEl.style.transform = 'translateY(-6px)';
    bannerEl.style.opacity = '0';
    setTimeout(()=>{ bannerEl.style.transform='translateY(0)'; bannerEl.style.opacity='1'; }, 180);
  };

  // Button microinteractions
  Animations.chargeStart = btn => {
    if (!btn) return;
    btn.style.transition='transform 120ms ease';
    btn.style.transform='scale(0.98)';
    setTimeout(()=>btn.style.transform='scale(1)',120);
    if (navigator.vibrate) navigator.vibrate([12]);
  };

  // Wallet number tween
  Animations.chargeStop = (el, fromVal, toVal) => {
    if (!el) return;
    const start = performance.now(), dur = 800;
    const from = Number(fromVal||0), to = Number(toVal||0);
    const step = t => {
      const p = Math.min(1, (t-start)/dur);
      const eased = 1 - Math.pow(1-p,3);
      const v = from + (to-from)*eased;
      el.textContent = `$${v.toFixed(2)}`;
      if (p<1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
    if (navigator.vibrate) navigator.vibrate([6,40,12]);
  };

  // Green Hour pulse on Start button
  let pulseOn = false;
  Animations.greenPulse = btn => {
    if (!btn) return;
    if (!document.getElementById('nerava-anim-style')) {
      const st = document.createElement('style');
      st.id='nerava-anim-style';
      st.textContent = `
        .pulse-green{ box-shadow:0 0 0 0 rgba(50,198,113,.6); animation:nerava-pulse 1.6s ease-out infinite; }
        @keyframes nerava-pulse{ 0%{box-shadow:0 0 0 0 rgba(50,198,113,.55);} 70%{box-shadow:0 0 0 14px rgba(50,198,113,0);} 100%{box-shadow:0 0 0 0 rgba(50,198,113,0);} }
        .checkbox-pop{ transition: transform 120ms ease; }
        .checkbox-pop.pop{ transform: scale(1.1); }
        .wallet-progress{ height:10px; border-radius:999px; overflow:hidden; background:#e5e7eb; }
        .wallet-progress > .bar{ height:100%; width:0; background:#22c55e; transition: width 1s ease-out; }
      `;
      document.head.appendChild(st);
    }
    btn.classList.add('pulse-green'); pulseOn = true;
  };
  Animations.stopGreenPulse = btn => { if (!btn) return; btn.classList.remove('pulse-green'); pulseOn=false; };

  // Confetti on streak up
  Animations.streakCelebrate = () => {
    const n = 18;
    for (let i=0;i<n;i++){
      const d = document.createElement('div');
      d.style.cssText = `position:fixed;top:12%;left:50%;width:6px;height:10px;border-radius:2px;
      background:hsl(${Math.floor(Math.random()*360)},80%,60%);transform:translateX(-50%);z-index:3000;pointer-events:none;`;
      document.body.appendChild(d);
      ((el,idx)=>{
        const dx=(Math.random()*2-1)*140, dy=260+Math.random()*120, rot=(Math.random()*2-1)*540;
        el.animate([{transform:`translate(-50%,0) rotate(0)`,opacity:1},{transform:`translate(calc(-50% + ${dx}px),${dy}px) rotate(${rot}deg)`,opacity:0}],
          {duration:900+Math.random()*400,easing:'cubic-bezier(.22,1,.36,1)',fill:'forwards',delay:idx*8});
        setTimeout(()=>el.remove(),1600);
      })(d,i);
    }
    if (navigator.vibrate) navigator.vibrate([10,30,10]);
  };

  window.Animations = Animations;
})();