'use client'

import Image from 'next/image'
import SectionWrapper from './SectionWrapper'
import { PrimaryButton } from '../Button'

export default function DriversSection() {
  const features = [
    {
      title: 'Charge anywhere, earn Nova',
      description: 'Off-peak or mission-based charging earns Nova automatically. No extra steps, no complicated processes – just plug in during optimal times and watch your rewards accumulate.',
    },
    {
      title: 'Spend Nova at real places',
      description: 'Use Nova at coffee shops, gyms, restaurants, and more as we expand the network. Your rewards work where you actually spend time, not just online.',
    },
    {
      title: 'Unlock streak rewards',
      description: 'For drivers who consistently charge off-peak, Nova streaks sometimes unlock Starbucks, Target, or other branded rewards via digital gift cards. Consistency pays off.',
    },
    {
      title: 'Simple, transparent rewards',
      description: 'No weird tokens, no withdrawal headaches. You earn Nova and use it to lower what you pay at places you already go. Clear rules, predictable value, instant savings.',
    },
  ]

  return (
    <SectionWrapper id="drivers" className="bg-gray-50">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        <div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
            For Drivers — Get Paid to Charge Smarter
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            Transform every charging session into tangible value. Nerava rewards you for 
            making grid-friendly choices while giving you spending power at the places you 
            already love. It's that simple.
          </p>
          
          <div className="space-y-6 mb-8">
            {features.map((feature, index) => (
              <div key={index}>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
          
          <PrimaryButton href="#final-cta">
            Join the driver waitlist
          </PrimaryButton>
          <p className="text-sm text-gray-500 mt-2">
            Be first in line when we launch in your city
          </p>
        </div>
        
        <div className="relative w-full h-[500px] rounded-lg overflow-hidden shadow-xl">
          <Image
            src="/landing/v2/3_For-Drivers-Get-Paid-to-Charge-Smarter.jpeg"
            alt="EV driver earning rewards"
            fill
            className="object-cover"
          />
        </div>
      </div>
    </SectionWrapper>
  )
}

