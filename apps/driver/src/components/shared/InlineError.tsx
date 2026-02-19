// Inline error component — replaces alert() calls with contextual, dismissible errors
import { useState, useEffect } from 'react'
import { AlertCircle, X } from 'lucide-react'

interface InlineErrorProps {
  message: string | null
  onDismiss?: () => void
  /** Auto-dismiss after N ms. 0 = never. Default 8000. */
  autoDismissMs?: number
  className?: string
}

/**
 * Contextual error message displayed inline near the action that failed.
 * Replaces browser alert() with a styled, dismissible banner.
 */
export function InlineError({
  message,
  onDismiss,
  autoDismissMs = 8000,
  className = '',
}: InlineErrorProps) {
  const [visible, setVisible] = useState(!!message)

  useEffect(() => {
    if (message) {
      setVisible(true)
      if (autoDismissMs > 0) {
        const timer = setTimeout(() => {
          setVisible(false)
          onDismiss?.()
        }, autoDismissMs)
        return () => clearTimeout(timer)
      }
    } else {
      setVisible(false)
    }
  }, [message, autoDismissMs, onDismiss])

  if (!message || !visible) return null

  return (
    <div
      className={`flex items-start gap-2 bg-red-50 border border-red-200 rounded-xl px-4 py-3 ${className}`}
      role="alert"
    >
      <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <p className="text-sm text-red-700 flex-1">{message}</p>
      {onDismiss && (
        <button
          onClick={() => {
            setVisible(false)
            onDismiss()
          }}
          className="flex-shrink-0 p-1 hover:bg-red-100 rounded-full transition-colors"
          aria-label="Dismiss error"
        >
          <X className="w-3.5 h-3.5 text-red-400" />
        </button>
      )}
    </div>
  )
}
