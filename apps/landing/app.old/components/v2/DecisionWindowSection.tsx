import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'

export default function DecisionWindowSection() {
  const points = [
    {
      title: 'Time to decide',
      description: 'Every charging session creates a 15-45 minute window where drivers need to decide what to do.',
    },
    {
      title: 'High-intent moment',
      description: 'Drivers are already nearby, actively looking for ways to spend their time and money.',
    },
    {
      title: 'Discovery gap',
      description: 'Most drivers don\'t know what\'s walkable nearby, leading to missed opportunities for both drivers and local businesses.',
    },
    {
      title: 'Zero-friction opportunity',
      description: 'The right information at the right moment can turn idle time into meaningful local commerce.',
    },
  ]

  return (
    <SectionWrapper id="decision-window">
      <SectionHeader
        title="Charging creates a decision window"
        subtitle="Every time an EV driver plugs in, a moment of opportunity opens. They're nearby, they have time, and they're ready to discover what's around them."
      />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
        {points.map((point, index) => (
          <div
            key={index}
            className="bg-gray-50 rounded-lg p-6 hover:shadow-md transition-shadow"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {point.title}
            </h3>
            <p className="text-gray-600">
              {point.description}
            </p>
          </div>
        ))}
      </div>
    </SectionWrapper>
  )
}



