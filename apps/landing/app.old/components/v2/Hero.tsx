'use client'

import { useState, useEffect } from 'react'
import SectionWrapper from './SectionWrapper'
import { PrimaryButton } from '../Button'
import { getDriverCTAHref, getMerchantCTAHref, CHARGER_OWNER_CTA_HREF } from './ctaLinks'
import { captureCTAClick } from '../../analytics/posthog'

export default function Hero() {
  const [driverHref, setDriverHref] = useState('')
  const [merchantHref, setMerchantHref] = useState('')

  useEffect(() => {
    setDriverHref(getDriverCTAHref())
    setMerchantHref(getMerchantCTAHref())
  }, [])

  return (
    <SectionWrapper className="bg-gradient-to-b from-primary-soft to-white py-20 sm:py-24 lg:py-32">
      <div className="max-w-5xl mx-auto text-center">
        <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 mb-4 break-words">
          Nerava
        </h1>
        <p className="text-2xl sm:text-3xl md:text-4xl font-semibold text-gray-800 mb-3">
          What to do while you charge.
        </p>
        <p className="text-xl sm:text-2xl text-gray-600 mb-12 font-medium">
          Discover exclusive experiences at charging stations near you.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-6">
          <PrimaryButton 
            href={driverHref || getDriverCTAHref()}
            className="w-full sm:w-auto min-w-[200px]"
            onClick={() => captureCTAClick('open_driver', 'Open Nerava', driverHref || getDriverCTAHref())}
          >
            Open Nerava
          </PrimaryButton>
          <PrimaryButton 
            href={merchantHref || getMerchantCTAHref()}
            className="w-full sm:w-auto min-w-[200px]"
            onClick={() => captureCTAClick('for_businesses', 'For Businesses', merchantHref || getMerchantCTAHref())}
          >
            For Businesses
          </PrimaryButton>
        </div>
        
        <p className="text-sm text-gray-600">
          <a 
            href={CHARGER_OWNER_CTA_HREF}
            className="underline hover:text-primary transition-colors"
          >
            I'm a Charger Owner
          </a>
        </p>
      </div>
    </SectionWrapper>
  )
}

