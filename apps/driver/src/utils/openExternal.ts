/**
 * Open an external URL.
 * In the iOS WKWebView, uses the native bridge to open in Safari.
 * Otherwise, falls back to window.open.
 */
export function openExternalUrl(url: string) {
  // Check if running inside the iOS WKWebView with native bridge
  if ((window as any).neravaNative?.openExternalUrl) {
    ;(window as any).neravaNative.openExternalUrl(url)
  } else {
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}
