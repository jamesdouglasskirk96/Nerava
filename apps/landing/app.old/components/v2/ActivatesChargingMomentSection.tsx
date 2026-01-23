import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'

export default function ActivatesChargingMomentSection() {
  const features = [
    {
      title: 'Detects active charging',
      description: 'Nerava automatically knows when you\'re charging, so you don\'t have to think about it.',
    },
    {
      title: 'Surfaces walkable businesses nearby',
      description: 'See coffee shops, restaurants, gyms, and stores within walking distance of your charger.',
    },
    {
      title: 'Helps drivers decide instantly',
      description: 'No search, no scrolling, no guessing. Just clear options tailored to your charging moment.',
    },
  ]

  return (
    <SectionWrapper id="activates-moment" className="bg-gray-50">
      <SectionHeader
        title="Nerava activates the charging moment"
        subtitle="We turn idle charging time into discovery opportunities by connecting drivers with nearby businesses at exactly the right moment."
      />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        {features.map((feature, index) => (
          <div
            key={index}
            className="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              {feature.title}
            </h3>
            <p className="text-gray-600">
              {feature.description}
            </p>
          </div>
        ))}
      </div>
    </SectionWrapper>
  )
}



