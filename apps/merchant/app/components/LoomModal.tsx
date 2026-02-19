import { useEffect, useRef, useCallback } from 'react'
import { capture } from '../analytics'
import { MERCHANT_EVENTS } from '../analytics/events'

const LOOM_URL = import.meta.env.VITE_LOOM_VIDEO_URL || 'https://www.loom.com/embed/placeholder'

interface LoomModalProps {
  merchantId: string
  open: boolean
  onClose: () => void
}

export function LoomModal({ merchantId, open, onClose }: LoomModalProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null)

  const handleClose = useCallback(() => {
    localStorage.setItem(`loom_seen_${merchantId}`, 'true')
    capture(MERCHANT_EVENTS.FUNNEL_LOOM_CLOSED, { merchant_id: merchantId })
    onClose()
  }, [merchantId, onClose])

  // Listen for Loom postMessage completion
  useEffect(() => {
    if (!open) return

    capture(MERCHANT_EVENTS.FUNNEL_LOOM_OPENED, { merchant_id: merchantId })

    function handleMessage(event: MessageEvent) {
      if (typeof event.data === 'string' && event.data.includes('loom') && event.data.includes('complete')) {
        capture(MERCHANT_EVENTS.FUNNEL_LOOM_COMPLETED, { merchant_id: merchantId })
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [open, merchantId])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') handleClose()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [open, handleClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={handleClose}
    >
      <div
        className="relative w-full max-w-3xl bg-black rounded-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={handleClose}
          className="absolute top-3 right-3 z-10 w-8 h-8 rounded-full bg-white/20 hover:bg-white/40 flex items-center justify-center text-white transition-colors"
          aria-label="Close"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* 16:9 iframe container */}
        <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
          <iframe
            ref={iframeRef}
            src={LOOM_URL}
            className="absolute inset-0 w-full h-full"
            frameBorder="0"
            allow="autoplay; fullscreen"
            allowFullScreen
            title="Nerava demo video"
          />
        </div>

        {/* Fallback link */}
        <div className="p-3 text-center">
          <a
            href={LOOM_URL.replace('/embed/', '/share/')}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-white/70 hover:text-white underline"
          >
            Watch demo in new tab
          </a>
        </div>
      </div>
    </div>
  )
}
