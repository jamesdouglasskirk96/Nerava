import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'
import { PrimaryButton } from '../Button'
import { DRIVER_CTA_HREF } from './ctaLinks'

export default function DriversSection() {
  const features = [
    {
      title: 'Works quietly in the background',
      description: 'Nerava detects when you\'re charging and surfaces nearby businesses automatically. No searching, no scrolling—just clear options when you need them.',
    },
    {
      title: 'Discover walkable places',
      description: 'See coffee shops, restaurants, gyms, and stores within walking distance of your charger. Turn charging time into discovery time.',
    },
    {
      title: 'Instant decisions',
      description: 'Get the information you need to decide quickly. No guessing, no research—just actionable options tailored to your charging moment.',
    },
  ]

  return (
    <SectionWrapper id="drivers">
      <SectionHeader
        title="For drivers"
        subtitle="Nerava works quietly in the background, surfacing nearby businesses exactly when you need them during your charging session."
      />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto mb-10">
        {features.map((feature, index) => (
          <div
            key={index}
            className="bg-gray-50 rounded-lg p-6 hover:shadow-md transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              {feature.title}
            </h3>
            <p className="text-gray-600">
              {feature.description}
            </p>
          </div>
        ))}
      </div>
      
      <div className="text-center">
        <PrimaryButton href={DRIVER_CTA_HREF}>
          Join the driver waitlist
        </PrimaryButton>
      </div>
    </SectionWrapper>
  )
}

