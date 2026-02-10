import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { DriverSessionProvider } from './contexts/DriverSessionContext'
import { FavoritesProvider } from './contexts/FavoritesContext'
import { DriverHome } from './components/DriverHome/DriverHome'
import { OnboardingGate } from './components/Onboarding/OnboardingGate'
import { OfflineBanner } from './components/shared/OfflineBanner'
import { ConsentBanner } from './components/ConsentBanner'
import { useViewportHeight } from './hooks/useViewportHeight'
// Keep existing routes for backward compatibility
import { WhileYouChargeScreen } from './components/WhileYouCharge/WhileYouChargeScreen'
import { MerchantDetailsScreen } from './components/MerchantDetails/MerchantDetailsScreen'
import { MerchantArrivalScreen } from './components/EVArrival/MerchantArrivalScreen'
import { PreChargingScreen } from './components/PreCharging/PreChargingScreen'
import { EVHome } from './components/EVHome/EVHome'
import { EVOrderFlow } from './components/EVOrder/EVOrderFlow'
import { PhoneCheckinScreen } from './components/PhoneCheckin'

function App() {
  useViewportHeight()
  
  // Set basename for React Router - Vite provides BASE_URL from base config
  // BASE_URL is '/app/' when built with VITE_PUBLIC_BASE=/app/, '/' in dev
  const basename = import.meta.env.BASE_URL || '/app'
  
  return (
    <FavoritesProvider>
      <DriverSessionProvider>
        <OfflineBanner />
        <BrowserRouter basename={basename}>
        <OnboardingGate>
          <Routes>
            {/* Phone check-in route (from SMS link) */}
            <Route path="/s/:token" element={<PhoneCheckinScreen />} />
            {/* Main driver app route */}
            <Route path="/" element={<DriverHome />} />
            <Route path="/driver" element={<DriverHome />} />
            {/* EV-specific routes */}
            <Route path="/ev-home" element={<EVHome />} />
            <Route path="/ev-order" element={<EVOrderFlow />} />
            {/* Legacy routes for backward compatibility */}
            <Route path="/wyc" element={<WhileYouChargeScreen />} />
            <Route path="/pre-charging" element={<PreChargingScreen />} />
            {/* Phase 0 phone-first EV arrival flow */}
            <Route path="/m/:merchantId" element={<MerchantArrivalScreen />} />
            {/* Merchant details route */}
            <Route path="/merchant/:merchantId" element={<MerchantDetailsScreen />} />
          </Routes>
        </OnboardingGate>
      </BrowserRouter>
      <ConsentBanner />
    </DriverSessionProvider>
    </FavoritesProvider>
  )
}

export default App
