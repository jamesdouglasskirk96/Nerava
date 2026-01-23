import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'

export default function WhyNeravaWorksSection() {
  const reasons = [
    {
      title: 'High-intent',
      description: 'Drivers are actively charging and looking for ways to spend their time. This isn\'t passive browsing—it\'s a moment of active decision-making.',
    },
    {
      title: 'Proximity',
      description: 'Businesses are within walking distance of chargers. No driving needed, just a short walk to discover something new.',
    },
    {
      title: 'Zero friction',
      description: 'No search required, no scrolling through endless options. Nerava surfaces the right businesses at the right moment.',
    },
  ]

  return (
    <SectionWrapper id="why-works">
      <SectionHeader
        title="Why Nerava Works"
        subtitle="Three principles that make the charging moment perfect for local discovery"
      />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        {reasons.map((reason, index) => (
          <div
            key={index}
            className="text-center"
          >
            <h3 className="text-2xl font-bold text-primary mb-4">
              {reason.title}
            </h3>
            <p className="text-gray-600">
              {reason.description}
            </p>
          </div>
        ))}
      </div>
    </SectionWrapper>
  )
}



