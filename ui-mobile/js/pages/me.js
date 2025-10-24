// Me page logic
window.Nerava = window.Nerava || {};
window.Nerava.pages = window.Nerava.pages || {};

function addCheckboxPopAnimation() {
  const checkboxes = document.querySelectorAll('#pageMe input[type="checkbox"]');
  checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      if (window.Animations?.checkboxPop) {
        window.Animations.checkboxPop(checkbox);
      }
    });
  });
}

function initMe() {
  addCheckboxPopAnimation();
}

// Export init function
window.Nerava.pages.me = {
  init: initMe
};
