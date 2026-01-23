'use client'

import { useState, useEffect } from 'react'
import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'
import { PrimaryButton } from '../Button'
import { getDriverCTAHref, getMerchantCTAHref, CHARGER_OWNER_CTA_HREF } from './ctaLinks'
import { captureCTAClick } from '../../analytics/posthog'

export default function FinalCTA() {
  const [driverHref, setDriverHref] = useState('')
  const [merchantHref, setMerchantHref] = useState('')

  useEffect(() => {
    setDriverHref(getDriverCTAHref())
    setMerchantHref(getMerchantCTAHref())
  }, [])

  return (
    <SectionWrapper id="final-cta">
      <SectionHeader
        title="Be part of the charging moment"
        subtitle="Join the network that's transforming idle charging time into local discovery and commerce."
      />
      
      <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
        <PrimaryButton 
          href={driverHref || getDriverCTAHref()}
          className="w-full sm:w-auto min-w-[200px]"
          onClick={() => captureCTAClick('open_driver', "I'm a Driver", driverHref || getDriverCTAHref())}
        >
          I'm a Driver
        </PrimaryButton>
        <PrimaryButton 
          href={merchantHref || getMerchantCTAHref()}
          className="w-full sm:w-auto min-w-[200px]"
          onClick={() => captureCTAClick('for_businesses', "I'm a Merchant Near a Charger", merchantHref || getMerchantCTAHref())}
        >
          I'm a Merchant Near a Charger
        </PrimaryButton>
      </div>
      
      <div className="text-center pt-8 border-t border-gray-200">
        <p className="text-gray-600">
          <a 
            href={CHARGER_OWNER_CTA_HREF}
            className="text-primary hover:text-primary-dark underline font-semibold"
          >
            I'm a Charger Owner
          </a>
        </p>
      </div>
    </SectionWrapper>
  )
}

