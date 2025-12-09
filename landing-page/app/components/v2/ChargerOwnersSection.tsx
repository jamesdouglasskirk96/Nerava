import Image from 'next/image'
import SectionWrapper from './SectionWrapper'
import { SecondaryButton } from '../Button'

export default function ChargerOwnersSection() {
  const steps = [
    {
      icon: '📤',
      title: 'Upload your usage report',
      description: 'Share your charging data securely with our team',
    },
    {
      icon: '📊',
      title: 'We estimate off-peak potential',
      description: 'Identify optimization opportunities and quantify value',
    },
    {
      icon: '📍',
      title: 'We model demand around you',
      description: 'Assess driver incentives and merchant participation near your property',
    },
  ]

  return (
    <SectionWrapper id="charger-owners">
      <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-8 break-words">
        For Charger Owners & Properties
      </h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center mb-12">
        <div className="relative w-full h-[500px] rounded-lg overflow-hidden shadow-xl">
          <Image
            src="/landing/v2/8_For-Charger-Owners-and-Properties.png"
            alt="Property manager analyzing charging data"
            fill
            className="object-cover"
          />
        </div>
        
        <div>
          <p className="text-lg text-gray-700 mb-6">
            If you manage EV chargers at an apartment complex, hotel, corporate campus, or retail 
            property, understanding your charging patterns unlocks significant value. Nerava can analyze 
            your usage data to reveal how much off-peak potential exists and what it's worth – both for 
            your residents and your bottom line.
          </p>
          <p className="text-lg text-gray-700 mb-8">
            Our free usage report analysis examines your charging data to identify optimization 
            opportunities. We model driver incentive programs and estimate merchant demand around your 
            location, giving you a clear picture of how Nerava could enhance your property's value proposition.
          </p>
          
          <div className="bg-primary-soft rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Property Benefits</h3>
            <p className="text-gray-700">
              Optimize charger utilization, reduce peak demand charges, and enhance resident satisfaction.
            </p>
          </div>
        </div>
      </div>
      
      <div className="mb-8">
        <h3 className="text-xl font-bold text-gray-900 mb-6 text-center">
          How It Works
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {steps.map((step, index) => (
            <div
              key={index}
              className="bg-gray-50 rounded-lg p-6 text-center"
            >
              <div className="text-4xl mb-4">{step.icon}</div>
              <h4 className="text-lg font-semibold text-gray-900 mb-2">
                {step.title}
              </h4>
              <p className="text-gray-600 text-sm">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
      
      <div className="text-center">
        <SecondaryButton 
          href="https://forms.gle/2HY3p3882yhqMkT69"
        >
          Get a free usage report review
        </SecondaryButton>
      </div>
    </SectionWrapper>
  )
}

