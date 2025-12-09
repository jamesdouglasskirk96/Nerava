import Image from 'next/image'
import SectionWrapper from './SectionWrapper'

export default function WhyNeravaMatters() {
  const cards = [
    {
      title: 'For Drivers',
      description: 'Real rewards for charging smarter. Grid-friendly behavior translates into immediate spending power at places like coffee shops, gyms, and restaurants, making charging a source of ongoing value.',
    },
    {
      title: 'Merchants',
      description: 'Tap into a growing, high-value customer base with precise targeting. Nerava brings nearby EV drivers through your doors with built-in incentives, and you only pay for actual redemptions.',
    },
    {
      title: 'For the Grid',
      description: 'Incentivize demand response at scale. Off-peak charging reduces strain, maximizes renewable energy use, and creates a more resilient energy system, making grid-friendly behavior economically attractive.',
    },
  ]

  return (
    <SectionWrapper>
      <div className="mb-12">
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-6">
          Why Nerava Matters
        </h2>
        <div className="flex items-start gap-4 mb-8">
          <div className="w-1 bg-primary h-full min-h-[60px]"></div>
          <p className="text-xl text-gray-700 italic max-w-3xl">
            &quot;We turn EV charging behavior into real-world commerce — and everyone wins.&quot;
          </p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12">
        <div className="space-y-6">
          <p className="text-lg text-gray-700">
            Electric vehicle adoption is accelerating rapidly, creating an unprecedented energy load 
            on the grid. Utilities need drivers to charge at optimal times to prevent grid strain and 
            maximize renewable energy use. But asking drivers to change behavior without meaningful 
            incentives is ineffective.
          </p>
          <p className="text-lg text-gray-700">
            Drivers need &apos;real&apos; rewards – tangible value they can use today, not abstract &apos;green points&apos; 
            or vague environmental promises. And local merchants need new, cost-effective customer 
            acquisition strategies that avoid expensive advertising or blanket discounting.
          </p>
        </div>
        
        <div className="relative w-full h-[400px] rounded-lg overflow-hidden shadow-xl">
          <Image
            src="/landing/v2/6_Why-Nerava-Matters.png"
            alt="Sustainable city with EV charging"
            fill
            className="object-cover"
          />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
        {cards.map((card, index) => (
          <div
            key={index}
            className="bg-gray-50 rounded-lg p-6"
          >
            <h3 className="text-lg font-bold text-gray-900 mb-3">
              {card.title}
            </h3>
            <p className="text-gray-600">
              {card.description}
            </p>
          </div>
        ))}
      </div>
      
      <div className="mt-12 p-6 bg-primary-soft rounded-lg">
        <p className="text-lg text-gray-800">
          Nerava sits at the intersection of these three forces, creating a sustainable marketplace 
          where charging behavior drives local commerce. Drivers earn Nova for charging smarter, spend 
          Nova at merchants who accept it, and merchants gain customers. This system is naturally 
          reinforcing and aligns incentives across all participants.
        </p>
      </div>
    </SectionWrapper>
  )
}

