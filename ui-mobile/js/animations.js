// Animation utilities for enhanced UX
(() => {
  'use strict';

  // ==== Animation Helpers ====
  
  function animatePulse(el, color = '#32C671') {
    if (!el) return;
    
    const originalBg = el.style.backgroundColor;
    const originalTransform = el.style.transform;
    
    el.style.transition = 'all 0.3s ease';
    el.style.backgroundColor = color;
    el.style.transform = 'scale(1.05)';
    
    setTimeout(() => {
      el.style.backgroundColor = originalBg;
      el.style.transform = originalTransform;
    }, 300);
  }
  
  function animateBounce(el) {
    if (!el) return;
    
    const originalTransform = el.style.transform;
    el.style.transition = 'transform 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55)';
    el.style.transform = 'scale(1.1)';
    
    setTimeout(() => {
      el.style.transform = originalTransform;
    }, 400);
  }
  
  function animateNumberCounter(el, start, end, duration = 1000) {
    if (!el) return;
    
    const startTime = performance.now();
    const difference = end - start;
    
    function updateNumber(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function for smooth animation
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = start + (difference * easeOut);
      
      el.textContent = `$${current.toFixed(2)}`;
      
      if (progress < 1) {
        requestAnimationFrame(updateNumber);
      }
    }
    
    requestAnimationFrame(updateNumber);
  }
  
  function animateProgressBar(el, targetPercent, duration = 800) {
    if (!el) return;
    
    const startTime = performance.now();
    const startPercent = parseFloat(el.style.width) || 0;
    const difference = targetPercent - startPercent;
    
    function updateProgress(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      const easeOut = 1 - Math.pow(1 - progress, 2);
      const current = startPercent + (difference * easeOut);
      
      el.style.width = `${current}%`;
      
      if (progress < 1) {
        requestAnimationFrame(updateProgress);
      }
    }
    
    requestAnimationFrame(updateProgress);
  }
  
  // ==== Haptic Feedback ====
  
  function vibrate(pattern = [12]) {
    if (navigator.vibrate) {
      navigator.vibrate(pattern);
    }
  }
  
  // ==== CSS Animation Classes ====
  
  function addAnimationClass(el, className, duration = 1000) {
    if (!el) return;
    
    el.classList.add(className);
    setTimeout(() => {
      el.classList.remove(className);
    }, duration);
  }
  
  // ==== Integration Helpers ====
  
  function animateChargeStart(buttonEl) {
    animatePulse(buttonEl, '#32C671');
    vibrate([12]);
    addAnimationClass(buttonEl, 'pulse-glow');
  }
  
  function animateChargeStop(walletEl, oldBalance, newBalance) {
    animateBounce(walletEl);
    animateNumberCounter(walletEl, oldBalance, newBalance);
    vibrate([8, 4, 8]);
  }
  
  function animateBannerTransition(bannerEl) {
    addAnimationClass(bannerEl, 'fade-in');
  }
  
  function animateProgressUpdate(progressEl, newPercent) {
    animateProgressBar(progressEl, newPercent);
  }
  
  // ==== Expose to Global Scope ====
  
  window.Animations = {
    pulse: animatePulse,
    bounce: animateBounce,
    counter: animateNumberCounter,
    progress: animateProgressUpdate,
    vibrate: vibrate,
    chargeStart: animateChargeStart,
    chargeStop: animateChargeStop,
    bannerTransition: animateBannerTransition,
    addClass: addAnimationClass
  };
  
})();
