/**
 * Analytics Debug Panel (Dev Only)
 * 
 * Temporary debug panel to test analytics events and view last event payload.
 * Only renders in development mode.
 */

import { useState, useEffect } from 'react'
import { capture, identify } from '../../analytics'
import posthog from 'posthog-js'

export function AnalyticsDebugPanel() {
  const [lastEvent, setLastEvent] = useState<{
    event: string
    properties: Record<string, unknown>
  } | null>(null)

  // Only render in dev mode
  if (import.meta.env.MODE === 'production') {
    return null
  }

  // Listen for PostHog events (hacky but works for debugging)
  useEffect(() => {
    const originalCapture = posthog.capture
    posthog.capture = function(event: string, properties?: Record<string, unknown>) {
      setLastEvent({ event, properties: properties || {} })
      return originalCapture.call(this, event, properties)
    }
    
    return () => {
      posthog.capture = originalCapture
    }
  }, [])

  const handleTestEvent = () => {
    capture('driver.debug.test_event', {
      test_property: 'test_value',
      timestamp: new Date().toISOString(),
    })
  }

  const handleTestIdentify = () => {
    identify('test_driver_123', {
      test_trait: 'test_value',
      test_role: 'driver',
    })
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white border-2 border-gray-300 rounded-lg shadow-lg p-4 max-w-md z-50">
      <h3 className="text-lg font-bold mb-2">Analytics Debug Panel</h3>
      
      <div className="space-y-2 mb-4">
        <button
          onClick={handleTestEvent}
          className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Capture Test Event
        </button>
        
        <button
          onClick={handleTestIdentify}
          className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Identify Test User
        </button>
      </div>

      {lastEvent && (
        <div className="mt-4 border-t pt-4">
          <h4 className="font-semibold mb-2">Last Event:</h4>
          <div className="bg-gray-100 p-2 rounded text-xs font-mono overflow-auto max-h-48">
            <div className="mb-1">
              <strong>Event:</strong> {lastEvent.event}
            </div>
            <div>
              <strong>Properties:</strong>
              <pre className="mt-1 whitespace-pre-wrap">
                {JSON.stringify(lastEvent.properties, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}

      <div className="mt-4 text-xs text-gray-500">
        <div>Distinct ID: {posthog.get_distinct_id() || 'N/A'}</div>
        <div>PostHog Loaded: {posthog.__loaded ? 'Yes' : 'No'}</div>
      </div>
    </div>
  )
}




