import Hero from './components/v2/Hero'
import DecisionWindowSection from './components/v2/DecisionWindowSection'
import ActivatesChargingMomentSection from './components/v2/ActivatesChargingMomentSection'
import DriversSection from './components/v2/DriversSection'
import MerchantsSection from './components/v2/MerchantsSection'
import SponsorsSection from './components/v2/SponsorsSection'
import WhyNeravaWorksSection from './components/v2/WhyNeravaWorksSection'
import BuiltToScaleSection from './components/v2/BuiltToScaleSection'
import DownloadSection from './components/v2/DownloadSection'
import FinalCTA from './components/v2/FinalCTA'

export default function Home() {
  return (
    <main className="bg-white text-foreground">
      <Hero />
      <DecisionWindowSection />
      <ActivatesChargingMomentSection />
      <DriversSection />
      <MerchantsSection />
      <SponsorsSection />
      <WhyNeravaWorksSection />
      <BuiltToScaleSection />
      <DownloadSection />
      <FinalCTA />
    </main>
  )
}
