import Hero from './components/v2/Hero'
import HowItWorks from './components/v2/HowItWorks'
import DriversSection from './components/v2/DriversSection'
import MerchantsSection from './components/v2/MerchantsSection'
import NovaSection from './components/v2/NovaSection'
import WhyNeravaMatters from './components/v2/WhyNeravaMatters'
import WhoNeravaIsBuiltFor from './components/v2/WhoNeravaIsBuiltFor'
import ChargerOwnersSection from './components/v2/ChargerOwnersSection'
import AdvantageSection from './components/v2/AdvantageSection'
import FinalCTA from './components/v2/FinalCTA'

export default function Home() {
  return (
    <main className="bg-white text-gray-900">
      <Hero />
      <HowItWorks />
      <DriversSection />
      <MerchantsSection />
      <NovaSection />
      <WhyNeravaMatters />
      <WhoNeravaIsBuiltFor />
      <ChargerOwnersSection />
      <AdvantageSection />
      <FinalCTA />
    </main>
  )
}

