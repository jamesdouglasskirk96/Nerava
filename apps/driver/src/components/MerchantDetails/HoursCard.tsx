import { Clock } from 'lucide-react'

interface HoursCardProps {
  hoursText?: string  // e.g., "11 AM–11 PM · Open now" or "11 AM–11 PM · Closed"
  openNow?: boolean
  hoursToday?: string  // e.g., "11 AM–11 PM"
}

export function HoursCard({ hoursText, openNow, hoursToday }: HoursCardProps) {
  // Build hours text from available data
  let displayText = hoursText
  
  if (!displayText && hoursToday) {
    const status = openNow !== undefined ? (openNow ? 'Open now' : 'Closed') : ''
    displayText = status ? `${hoursToday} · ${status}` : hoursToday
  }

  // Note: Hours data is not currently in MerchantDetailsResponse type
  // This component accepts hours data if available, but API may not provide it
  if (!displayText) {
    return null
  }

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
      <div className="flex items-center gap-3">
        <Clock className="w-5 h-5 text-gray-600 flex-shrink-0" />
        <div>
          <p className="text-xs text-gray-500 mb-1.5 font-medium uppercase tracking-wide">Hours Today</p>
          <p className="text-sm text-gray-900">{displayText}</p>
        </div>
      </div>
    </div>
  )
}

