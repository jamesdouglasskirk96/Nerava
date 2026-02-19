'use client'
import { useEffect, useState } from 'react'
import { getDriverCTAHref } from './v2/ctaLinks'

export function MobileRedirectBanner() {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const ua = navigator.userAgent
    setIsMobile(/iPhone|iPad|iPod|Android/i.test(ua))
  }, [])

  if (!isMobile) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-[#2952E8] text-white p-4 z-50 flex items-center justify-between shadow-lg">
      <span className="text-sm font-medium">Open Nerava to find deals while you charge</span>
      <a
        href={getDriverCTAHref()}
        className="bg-white text-[#2952E8] px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
      >
        Open App
      </a>
    </div>
  )
}
