import Image from 'next/image'
import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'

export default function AdvantageSection() {
  const metrics = [
    {
      value: '3x',
      label: 'Driver Engagement',
      subtext: 'Higher redemption rates than traditional loyalty programs due to real-time proximity and immediate value',
    },
    {
      value: '60%',
      label: 'Merchant ROI',
      subtext: 'Lower customer acquisition costs versus paid advertising with precise targeting to nearby EV drivers',
    },
    {
      value: '24/7',
      label: 'Grid Optimization',
      subtext: 'Continuous incentives driving off-peak charging behavior when the grid needs it most',
    },
  ]

  const benefits = [
    {
      icon: '🌐',
      title: 'Network Effects',
      description: 'More drivers attract more merchants. More merchants attract more drivers. The network becomes more valuable for everyone as it grows, creating natural momentum.',
    },
    {
      icon: '♻️',
      title: 'Self-Sustaining Economics',
      description: 'Merchants pay only for redemptions. Drivers earn through behavior. The platform takes a small percentage that reinvests in growth. No external subsidy required.',
    },
    {
      icon: '🎯',
      title: 'Precision Targeting',
      description: 'Location-based matching ensures drivers see relevant merchants near their charging locations. No wasted impressions, no irrelevant offers – just timely, contextual opportunities.',
    },
    {
      icon: '📈',
      title: 'Actionable Insights',
      description: 'Both drivers and merchants get clear visibility into their Nerava activity. Track earnings, redemptions, and patterns to optimize your participation over time.',
    },
  ]

  return (
    <SectionWrapper className="bg-gray-50">
      <SectionHeader
        title="The Nerava Advantage"
        subtitle="Unlike traditional loyalty programs or generic discount platforms, Nerava creates unique value by connecting three distinct groups with aligned incentives. Our network effects strengthen as more participants join, creating a sustainable marketplace that grows naturally."
      />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
        <div className="relative w-full h-[500px] rounded-lg overflow-hidden shadow-xl">
          <Image
            src="/landing/v2/9_The-Nerava-Advantage.png"
            alt="EV charging under solar panels"
            fill
            className="object-cover"
          />
        </div>
        
        <div className="space-y-8">
          {metrics.map((metric, index) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-6">
              <div className="text-4xl font-bold text-primary mb-2">
                {metric.value}
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {metric.label}
              </h3>
              <p className="text-gray-600">
                {metric.subtext}
              </p>
            </div>
          ))}
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {benefits.map((benefit, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-md p-6"
          >
            <div className="flex items-start gap-4">
              <div className="text-3xl">{benefit.icon}</div>
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">
                  {benefit.title}
                </h3>
                <p className="text-gray-600">
                  {benefit.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </SectionWrapper>
  )
}

