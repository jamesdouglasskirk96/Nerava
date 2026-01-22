import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { DriverSessionProvider } from './contexts/DriverSessionContext'
import { DriverHome } from './components/DriverHome/DriverHome'
import { QRHandler } from './components/QRHandler/QRHandler'
import { PartyClusterScreen } from './components/PartyCluster/PartyClusterScreen'
// Keep existing routes for backward compatibility
import { WhileYouChargeScreen } from './components/WhileYouCharge/WhileYouChargeScreen'
import { MerchantDetailsScreen } from './components/MerchantDetails/MerchantDetailsScreen'
import { PreChargingScreen } from './components/PreCharging/PreChargingScreen'
import { ExclusiveActiveScreen } from './components/ExclusiveActive/ExclusiveActiveScreen'
import { AccountScreen } from './components/Account/AccountScreen'

function App() {
  return (
    <DriverSessionProvider>
      <BrowserRouter>
        <Routes>
          {/* QR code entry point */}
          <Route path="/app/qr/:token" element={<QRHandler />} />
          {/* Party cluster page */}
          <Route path="/app/party" element={<PartyClusterScreen />} />
          {/* Main driver app route */}
          <Route path="/" element={<DriverHome />} />
          <Route path="/driver" element={<DriverHome />} />
          {/* Legacy routes for backward compatibility */}
          <Route path="/wyc" element={<WhileYouChargeScreen />} />
          <Route path="/pre-charging" element={<PreChargingScreen />} />
          <Route path="/m/:merchantId" element={<MerchantDetailsScreen />} />
          <Route path="/app/merchant/:merchantId" element={<MerchantDetailsScreen />} />
          {/* Exclusive Active screen - shown after activating an exclusive */}
          <Route path="/app/exclusive/:merchantId" element={<ExclusiveActiveScreen />} />
          {/* Account screen */}
          <Route path="/account" element={<AccountScreen />} />
        </Routes>
      </BrowserRouter>
    </DriverSessionProvider>
  )
}

export default App
