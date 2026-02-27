import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { DriverSessionProvider } from './contexts/DriverSessionContext'
import { FavoritesProvider } from './contexts/FavoritesContext'
import { DriverHome } from './components/DriverHome/DriverHome'
import { OnboardingGate } from './components/Onboarding/OnboardingGate'
import { OfflineBanner } from './components/shared/OfflineBanner'
import { ConsentBanner } from './components/ConsentBanner'
import { ErrorBoundary } from './components/ErrorBoundary'
import { SessionExpiredModal } from './components/SessionExpiredModal'
import { useViewportHeight } from './hooks/useViewportHeight'

// Lazy-loaded route components for code splitting
const TeslaCallbackScreen = lazy(() => import('./components/TeslaLogin/TeslaCallbackScreen').then(m => ({ default: m.TeslaCallbackScreen })))
const VehicleSelectScreen = lazy(() => import('./components/TeslaLogin/VehicleSelectScreen').then(m => ({ default: m.VehicleSelectScreen })))
const EVHome = lazy(() => import('./components/EVHome/EVHome').then(m => ({ default: m.EVHome })))
const EVOrderFlow = lazy(() => import('./components/EVOrder/EVOrderFlow').then(m => ({ default: m.EVOrderFlow })))
const PhoneCheckinScreen = lazy(() => import('./components/PhoneCheckin').then(m => ({ default: m.PhoneCheckinScreen })))
const WhileYouChargeScreen = lazy(() => import('./components/WhileYouCharge/WhileYouChargeScreen').then(m => ({ default: m.WhileYouChargeScreen })))
const MerchantDetailsScreen = lazy(() => import('./components/MerchantDetails/MerchantDetailsScreen').then(m => ({ default: m.MerchantDetailsScreen })))
const EarningsScreen = lazy(() => import('./components/Earnings/EarningsScreen').then(m => ({ default: m.EarningsScreen })))
const MerchantArrivalScreen = lazy(() => import('./components/EVArrival/MerchantArrivalScreen').then(m => ({ default: m.MerchantArrivalScreen })))
const PreChargingScreen = lazy(() => import('./components/PreCharging/PreChargingScreen').then(m => ({ default: m.PreChargingScreen })))

function App() {
  useViewportHeight()

  // Set basename for React Router - Vite provides BASE_URL from base config
  // BASE_URL is '/app/' when built with VITE_PUBLIC_BASE=/app/, '/' in dev
  const basename = import.meta.env.BASE_URL || '/app'

  return (
    <ErrorBoundary>
    <FavoritesProvider>
      <DriverSessionProvider>
        <OfflineBanner />
        <BrowserRouter basename={basename}>
        <OnboardingGate>
          <Suspense fallback={<div className="flex items-center justify-center h-screen"><div className="w-8 h-8 border-4 border-[#1877F2] border-t-transparent rounded-full animate-spin" /></div>}>
          <Routes>
            {/* Tesla OAuth callback and vehicle selection */}
            <Route path="/tesla-callback" element={<TeslaCallbackScreen />} />
            <Route path="/select-vehicle" element={<VehicleSelectScreen />} />
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
            {/* Earnings / transaction history */}
            <Route path="/earnings" element={<EarningsScreen />} />
            {/* Merchant details route */}
            <Route path="/merchant/:merchantId" element={<MerchantDetailsScreen />} />
          </Routes>
          </Suspense>
        </OnboardingGate>
      </BrowserRouter>
      <ConsentBanner />
      <SessionExpiredModal />
    </DriverSessionProvider>
    </FavoritesProvider>
    </ErrorBoundary>
  )
}

export default App
