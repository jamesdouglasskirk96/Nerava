'use client'

import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'
import { PrimaryButton } from '../Button'

export default function MerchantsSection() {
  const benefits = [
    {
      title: 'New customers already nearby',
      description: "EV drivers are sitting and waiting while their vehicles charge. Nerava's network routes them to your business with active incentives to come through your door. These are warm leads with time to spend and Nova to redeem.",
    },
    {
      title: 'Pay only when Nova is redeemed',
      description: "No monthly fees. No expensive hardware. No upfront costs. You're only billed when a driver actually redeems Nova at your location. This means every dollar you spend directly correlates with a transaction at your register.",
    },
    {
      title: 'Instant, QR-based redemption',
      description: "Put a Nerava QR at your counter. Drivers scan, apply Nova as a discount, and you make a sale. The entire process takes seconds and integrates seamlessly into your existing checkout flow.",
    },
    {
      title: 'Better than generic discounts',
      description: "You're not discounting randomly to anyone who walks by. You're rewarding people making grid-friendly choices who are already near your store and actively looking for places to spend their time.",
    },
    {
      title: 'Metrics that actually matter',
      description: 'Track redemptions, estimated incremental revenue, and repeat visits from EV drivers. Our merchant dashboard shows you exactly how Nerava drives real business value, not vanity metrics.',
    },
    {
      title: 'No hardware, no hassle',
      description: 'All you need is a QR code printout or display. No complex integrations, no new point-of-sale systems, no IT headaches. Set it up in minutes and start accepting Nova today.',
    },
  ]

  return (
    <SectionWrapper id="merchants">
      <SectionHeader
        title="For Merchants — Turn EV Charging Into Foot Traffic"
        subtitle="EV drivers are already nearby, waiting for their vehicles to charge. Nerava routes them directly to your business with built-in incentives to spend. You only pay when they actually redeem Nova at your location — no monthly fees, no expensive hardware, just real customers and measurable results."
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
        {benefits.map((benefit, index) => (
          <div
            key={index}
            className="bg-gray-50 rounded-lg p-6 hover:shadow-md transition-shadow"
          >
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              {benefit.title}
            </h3>
            <p className="text-gray-600 text-sm">
              {benefit.description}
            </p>
          </div>
        ))}
      </div>
      
      <div className="bg-primary-soft rounded-lg p-6 mb-6">
        <div className="flex items-start gap-4 mb-4">
          <div className="text-2xl">✓</div>
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-2">The Nova Flow</h4>
            <p className="text-gray-700">
              Driver redeems Nova → You provide a discount → You make a sale
            </p>
          </div>
        </div>
      </div>
      
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-center">
        <PrimaryButton href="#final-cta">
          Start accepting Nova
        </PrimaryButton>
        <a 
          href="mailto:founder@nerava.network?subject=Sample Merchant Report Request"
          className="text-primary hover:text-primary-dark underline"
        >
          See sample merchant report
        </a>
      </div>
    </SectionWrapper>
  )
}

