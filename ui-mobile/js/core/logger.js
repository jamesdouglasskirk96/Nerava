/**
 * Logger utility for frontend (P1-1: security hardening)
 * 
 * Prevents sensitive data from being logged in production.
 * Only logs in debug mode (non-prod environment with DEBUG flag).
 */

const DEBUG = (() => {
  const urlParams = new URLSearchParams(window.location.search);
  const env = urlParams.get('env') || localStorage.getItem('NERAVA_ENV') || 'prod';
  return env !== 'prod' && (urlParams.get('debug') === '1' || localStorage.getItem('NERAVA_DEBUG') === '1');
})();

/**
 * Sanitize string to remove sensitive data
 */
function sanitize(str) {
  if (typeof str !== 'string') {
    return str;
  }
  // Remove tokens
  str = str.replace(/Bearer\s+[\w-]+/gi, 'Bearer [REDACTED]');
  // Remove emails
  str = str.replace(/[\w.-]+@[\w.-]+\.\w+/g, '[EMAIL]');
  // Remove potential secrets (long base64-like strings)
  str = str.replace(/[A-Za-z0-9+/]{40,}={0,2}/g, '[SECRET]');
  return str;
}

/**
 * Log message (only in debug mode)
 */
export function log(...args) {
  if (DEBUG) {
    const sanitized = args.map(arg => {
      if (typeof arg === 'string') {
        return sanitize(arg);
      }
      if (typeof arg === 'object' && arg !== null) {
        try {
          const str = JSON.stringify(arg);
          return JSON.parse(sanitize(str));
        } catch {
          return arg;
        }
      }
      return arg;
    });
    console.log('[NERAVA]', ...sanitized);
  }
}

/**
 * Log error (always logs, but sanitizes sensitive data)
 */
export function error(...args) {
  const sanitized = args.map(arg => {
    if (typeof arg === 'string') {
      return sanitize(arg);
    }
    if (typeof arg === 'object' && arg !== null) {
      try {
        const str = JSON.stringify(arg);
        return JSON.parse(sanitize(str));
      } catch {
        return arg;
      }
    }
    return arg;
  });
  console.error('[NERAVA]', ...sanitized);
}

/**
 * Log warning (always logs, but sanitizes sensitive data)
 */
export function warn(...args) {
  const sanitized = args.map(arg => {
    if (typeof arg === 'string') {
      return sanitize(arg);
    }
    if (typeof arg === 'object' && arg !== null) {
      try {
        const str = JSON.stringify(arg);
        return JSON.parse(sanitize(str));
      } catch {
        return arg;
      }
    }
    return arg;
  });
  console.warn('[NERAVA]', ...sanitized);
}



