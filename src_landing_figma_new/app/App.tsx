import { Header } from './components/Header';
import { Hero } from './components/Hero';
import { Insight } from './components/Insight';
import { WhatNeravaDoes } from './components/WhatNeravaDoes';
import { ForDrivers } from './components/ForDrivers';
import { ForMerchants } from './components/ForMerchants';
import { WhyThisWorks } from './components/WhyThisWorks';
import { BuiltToScale } from './components/BuiltToScale';
import { FinalCTA } from './components/FinalCTA';
import { Footer } from './components/Footer';

export default function App() {
  return (
    <div className="min-h-screen bg-white">
      <Header />
      <Hero />
      <Insight />
      <WhatNeravaDoes />
      <ForDrivers />
      <ForMerchants />
      <WhyThisWorks />
      <BuiltToScale />
      <FinalCTA />
      <Footer />
    </div>
  );
}
