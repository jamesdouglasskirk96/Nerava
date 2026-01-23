import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'

export default function HowItWorks() {
  const steps = [
    {
      title: 'Charge Smarter',
      description: 'Connect your EV and get rewarded with Nova when you charge off-peak or complete missions. Every charging session during optimal times earns you instant rewards.',
      icon: '⚡',
    },
    {
      title: 'Earn Nova',
      description: 'Verified charging sessions and streaks earn Nova in the Nerava wallet – a universal reward currency tied to your charging behavior. Watch your balance grow with every smart charge.',
      icon: '💎',
    },
    {
      title: 'Spend at Merchants',
      description: "Scan a merchant's Nerava QR at checkout to apply Nova as an instant discount. Merchants pay only when Nova is redeemed, creating a win-win ecosystem.",
      icon: '📱',
    },
  ]

  return (
    <SectionWrapper id="how-it-works">
      <SectionHeader
        title="How Nerava Works"
        subtitle="A simple three-step system that transforms your charging routine into real-world rewards. Nerava creates a sustainable loop where smart charging decisions benefit drivers, merchants, and the energy grid alike."
      />
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {steps.map((step, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
          >
            <div className="text-4xl mb-4">{step.icon}</div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              {step.title}
            </h3>
            <p className="text-gray-600">
              {step.description}
            </p>
          </div>
        ))}
      </div>
    </SectionWrapper>
  )
}

