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
    <div className="bg-[#F7F8FA] rounded-2xl p-3 mb-4">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 bg-[#1877F2]/10 rounded-full flex items-center justify-center flex-shrink-0">
          <Clock className="w-4 h-4 text-[#1877F2]" />
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-sm mb-0.5">Hours Today</h3>
          <p className="text-xs text-[#65676B]">
            {displayText}
          </p>
        </div>
      </div>
    </div>
  )
}

