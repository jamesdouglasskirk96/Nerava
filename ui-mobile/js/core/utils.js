// Utility functions
window.Nerava = window.Nerava || {};
window.Nerava.core = window.Nerava.core || {};

// Format currency
function formatCurrency(cents) {
  return `$${(cents / 100).toFixed(2)}`;
}

// Format time
function formatTime(date) {
  return new Date(date).toLocaleTimeString([], {hour:'numeric', minute:'2-digit'});
}

// Debounce function
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Export to global namespace
window.Nerava.core.utils = {
  formatCurrency,
  formatTime,
  debounce
};
