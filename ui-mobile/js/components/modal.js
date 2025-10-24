// Accessibility: focus trap + ESC close
export function trapFocus(modal){ const focusables=modal.querySelectorAll('button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])'); const first=focusables[0]; const last=focusables[focusables.length-1];
  modal.addEventListener('keydown', (e)=>{ if(e.key==='Escape'){ modal.close?.(); } if(e.key!=='Tab')return;
    if(e.shiftKey && document.activeElement===first){ e.preventDefault(); last.focus(); }
    else if(!e.shiftKey && document.activeElement===last){ e.preventDefault(); first.focus(); }
  }); }

export function createModal(title, content) {
  const modal = document.createElement('dialog');
  modal.innerHTML = `
    <div class="modal-content">
      <h3>${title}</h3>
      <div class="modal-body">${content}</div>
      <button class="btn btn-secondary" onclick="this.closest('dialog').close()">Close</button>
    </div>
  `;
  return modal;
}

export function showModal(modal) {
  document.body.appendChild(modal);
  modal.showModal();
  trapFocus(modal);
}