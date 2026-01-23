import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { DriverSessionProvider } from './contexts/DriverSessionContext'
import { DriverHome } from './components/DriverHome/DriverHome'
import { OnboardingGate } from './components/Onboarding/OnboardingGate'
// Keep existing routes for backward compatibility
import { WhileYouChargeScreen } from './components/WhileYouCharge/WhileYouChargeScreen'
import { MerchantDetailsScreen } from './components/MerchantDetails/MerchantDetailsScreen'
import { PreChargingScreen } from './components/PreCharging/PreChargingScreen'

function App() {
  // Set basename for React Router - Vite provides BASE_URL from base config
  // BASE_URL is '/app/' when built with VITE_PUBLIC_BASE=/app/, '/' in dev
  const basename = import.meta.env.BASE_URL || '/app'
  
  return (
    <DriverSessionProvider>
      <BrowserRouter basename={basename}>
        <OnboardingGate>
          <Routes>
            {/* Main driver app route */}
            <Route path="/" element={<DriverHome />} />
            <Route path="/driver" element={<DriverHome />} />
            {/* Legacy routes for backward compatibility */}
            <Route path="/wyc" element={<WhileYouChargeScreen />} />
            <Route path="/pre-charging" element={<PreChargingScreen />} />
            <Route path="/m/:merchantId" element={<MerchantDetailsScreen />} />
          </Routes>
        </OnboardingGate>
      </BrowserRouter>
    </DriverSessionProvider>
  )
}

export default App
