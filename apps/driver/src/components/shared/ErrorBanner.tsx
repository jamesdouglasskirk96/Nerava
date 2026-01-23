// Error Banner component for displaying API errors with retry
import { AlertCircle } from 'lucide-react'
import { Button } from './Button'

interface ErrorBannerProps {
  message: string
  onRetry?: () => void
  isLoading?: boolean
}

export function ErrorBanner({ message, onRetry, isLoading = false }: ErrorBannerProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mx-4 my-4">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm text-red-800 font-medium mb-2">{message}</p>
          {onRetry && (
            <Button
              onClick={onRetry}
              disabled={isLoading}
              className="text-sm py-1.5 px-3 bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
            >
              {isLoading ? 'Retrying...' : 'Retry'}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}


