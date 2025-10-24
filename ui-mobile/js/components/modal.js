export function createModal(title, content) {
  const modal = document.createElement('dialog');
  modal.className = 'modal';
  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h3>${title}</h3>
        <button class="modal-close" aria-label="Close">&times;</button>
      </div>
      <div class="modal-body">
        ${content}
      </div>
    </div>
  `;
  
  const closeBtn = modal.querySelector('.modal-close');
  closeBtn.addEventListener('click', () => modal.close());
  
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.close();
  });
  
  return modal;
}

export function showModal(modal) {
  document.body.appendChild(modal);
  modal.showModal();
}

export function hideModal(modal) {
  modal.close();
  modal.remove();
}
