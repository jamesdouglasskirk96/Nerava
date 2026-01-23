import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'
import { PrimaryButton } from '../Button'
import { MERCHANT_CTA_HREF } from './ctaLinks'

export default function MerchantsSection() {
  const benefits = [
    {
      title: 'Pay only for charging-session impressions',
      description: 'Like Waze Local Ads, you only pay when drivers see your business during active charging sessions. No impressions when no one is charging nearby.',
    },
    {
      title: 'Set a daily cap — no contracts',
      description: 'Control your spend with daily budgets. No long-term commitments, no minimums. Start small and scale as you see results.',
    },
    {
      title: 'No POS integrations required',
      description: 'Simple QR code redemption. Drivers scan, you apply the discount, and you make the sale. Works with any payment system you already use.',
    },
  ]

  return (
    <SectionWrapper id="merchants" className="bg-gray-50">
      <SectionHeader
        title="For merchants near chargers"
        subtitle="Reach drivers at the perfect moment—when they're charging nearby and actively deciding what to do. Pay only for impressions during charging sessions, with full control over your daily spend."
      />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto mb-10">
        {benefits.map((benefit, index) => (
          <div
            key={index}
            className="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              {benefit.title}
            </h3>
            <p className="text-gray-600">
              {benefit.description}
            </p>
          </div>
        ))}
      </div>
      
      <div className="text-center">
        <PrimaryButton href={MERCHANT_CTA_HREF}>
          Start accepting Nova
        </PrimaryButton>
      </div>
    </SectionWrapper>
  )
}

