import Image from 'next/image'
import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'

export default function NovaSection() {
  const pillars = [
    {
      number: '01',
      title: 'Earned from behavior, not speculation',
      description: 'Nova is earned through verified EV charging behavior and completing missions, not by buying a token. Charging decisions directly translate into earning power. Off-peak charging, consistency streaks, and mission completion all generate Nova automatically.',
    },
    {
      number: '02',
      title: 'Closed-loop, merchant-backed',
      description: "Nova is only 'real' when a merchant accepts it as a discount, which keeps the system sustainable for everyone. Unlike points that can be orphaned or devalued, Nova's value is tied directly to merchant participation and real-world commerce.",
    },
    {
      number: '03',
      title: 'Safe and predictable',
      description: "Clear, transparent rules govern Nova's redemption value, ensuring no surprises for drivers or merchants. You always know what you're earning and what it can buy. No hidden fees, no conversion confusion, no fine print.",
    },
    {
      number: '04',
      title: 'Optional perks via branded rewards',
      description: 'Sometimes, Nova streaks unlock branded perks like Starbucks or Target gift cards, but the core loop is always charging → Nova → local commerce. These bonus rewards add extra value without complicating the fundamental system.',
    },
  ]

  return (
    <SectionWrapper className="bg-gray-50">
      <div className="mb-12">
        <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-2 text-center">
          What Is Nova?
        </p>
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-6 text-center">
          The Currency for Smarter Charging
        </h2>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-16">
        <div>
          <p className="text-lg text-gray-700 mb-4">
            Nova is the universal reward currency that powers the Nerava network. It's not a 
            cryptocurrency or speculative token, but a practical reward earned through verified 
            EV charging behavior and redeemed for real discounts at local merchants. Think of it 
            as loyalty points that work everywhere in the Nerava ecosystem.
          </p>
          <p className="text-lg text-gray-700">
            Every Nova in circulation is backed by actual charging behavior and merchant acceptance. 
            This is a closed-loop system ensuring sustainability, where drivers get predictable value, 
            merchants control their discount economics, and the grid benefits from smarter charging patterns.
          </p>
        </div>
        
        <div className="relative w-full h-[400px] rounded-lg overflow-hidden shadow-xl">
          <Image
            src="/landing/v2/5_What-Is-Nova.jpeg"
            alt="Nova currency ecosystem"
            fill
            className="object-cover"
          />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {pillars.map((pillar, index) => (
          <div
            key={index}
            className="bg-white rounded-lg shadow-md p-6"
          >
            <div className="flex items-start gap-4">
              <div className="text-3xl font-bold text-primary">{pillar.number}</div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  {pillar.title}
                </h3>
                <p className="text-gray-600">
                  {pillar.description}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </SectionWrapper>
  )
}

