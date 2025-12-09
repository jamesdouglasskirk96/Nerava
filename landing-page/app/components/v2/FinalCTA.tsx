import SectionWrapper from './SectionWrapper'
import SectionHeader from './SectionHeader'
import { PrimaryButton } from '../Button'

export default function FinalCTA() {
  return (
    <SectionWrapper id="final-cta">
      <SectionHeader
        title="Turn Every Charge Into an Opportunity"
        subtitle="Join the EV commerce revolution. Whether you drive an EV or serve EV drivers, Nerava connects smart charging behavior with real-world rewards."
      />
      
      <div className="mb-8">
        <p className="text-lg text-gray-700 text-center max-w-3xl mx-auto mb-10">
          Nerava is launching in select cities with high EV density. Join our waitlist to be among 
          the first to experience the future of EV rewards and commerce. Early adopters get exclusive 
          perks and priority access to new merchant partnerships. Our network is growing daily. The 
          sooner you join, the more merchants and drivers you'll connect with in your area.
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        <div className="bg-gray-50 rounded-lg p-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-3">
            For Drivers
          </h3>
          <p className="text-gray-600 mb-6">
            Start earning Nova with every smart charge
          </p>
          <PrimaryButton href="https://forms.gle/J6Rv2yo6uiQvH4pj7">
            Join the driver waitlist
          </PrimaryButton>
        </div>
        
        <div className="bg-gray-50 rounded-lg p-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-3">
            Merchants
          </h3>
          <p className="text-gray-600 mb-6">
            Attract new customers from nearby chargers
          </p>
          <PrimaryButton href="https://forms.gle/5gvVWqXrhSWwReDJA">
            Start accepting Nova
          </PrimaryButton>
        </div>
      </div>
      
      <div className="text-center pt-8 border-t border-gray-200">
        <p className="text-gray-600 mb-2">
          Charger owner or utility partner?{' '}
          <a 
            href="https://forms.gle/2HY3p3882yhqMkT69"
            className="text-primary hover:text-primary-dark underline font-semibold"
          >
            Get a free usage report review
          </a>
          {' '}to explore usage analytics and grid optimization opportunities.
        </p>
      </div>
    </SectionWrapper>
  )
}

