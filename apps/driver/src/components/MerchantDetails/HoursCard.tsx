import { Clock } from 'lucide-react'

interface HoursCardProps {
  hoursText?: string  // e.g., "7:00 AM - 8:00 PM · Open now"
  openNow?: boolean
  hoursToday?: string  // e.g., "7:00 AM - 8:00 PM"
}

export function HoursCard({ hoursText, openNow, hoursToday }: HoursCardProps) {
  // Build hours text from available data
  let displayText = hoursText

  if (!displayText && hoursToday) {
    const status = openNow !== undefined ? (openNow ? 'Open now' : 'Closed') : ''
    displayText = status ? `${hoursToday} · ${status}` : hoursToday
  }

  if (!displayText) {
    return null
  }

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
          <Clock className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-900">Hours Today</p>
          <p className="text-sm text-gray-600">{displayText}</p>
        </div>
      </div>
    </div>
  )
}

