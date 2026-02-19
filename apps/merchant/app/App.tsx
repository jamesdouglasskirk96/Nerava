import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { DemoNav } from './components/DemoNav';
import { ClaimBusiness } from './components/ClaimBusiness';
import { ClaimVerify } from './components/ClaimVerify';
import { SelectLocation } from './components/SelectLocation';
import { DashboardLayout } from './components/DashboardLayout';
import { Overview } from './components/Overview';
import { Exclusives } from './components/Exclusives';
import { CreateExclusive } from './components/CreateExclusive';
import { PrimaryExperience } from './components/PrimaryExperience';
import { PickupPackages } from './components/PickupPackages';
import { CreatePickupPackage } from './components/CreatePickupPackage';
import { Billing } from './components/Billing';
import { Settings } from './components/Settings';
import { CustomerExclusiveView } from './components/CustomerExclusiveView';
import { Visits } from './components/Visits';
import { ConsentBanner } from './components/ConsentBanner';
import { FindBusiness } from './components/FindBusiness';
import { MerchantPreview } from './components/MerchantPreview';
import { EVArrivals } from './components/EVArrivals';

export default function App() {
  // Support admin preview via URL params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const merchantIdParam = params.get('merchant_id');
    const adminPreview = params.get('admin_preview');
    
    if (merchantIdParam) {
      localStorage.setItem('merchant_id', merchantIdParam);
      if (adminPreview === 'true') {
        // Skip claim flow in admin preview mode
        localStorage.setItem('businessClaimed', 'true');
      }
    }
  }, []);

  // Simulating auth state - in real app this would come from context/state management
  const isClaimed = localStorage.getItem('businessClaimed') === 'true';
  
  // Set basename for React Router - Vite provides BASE_URL from base config
  // BASE_URL is '/merchant/' when built with VITE_PUBLIC_BASE=/merchant/, '/' in dev
  const basename = import.meta.env.BASE_URL || '/merchant';

  const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';

  return (
    <BrowserRouter basename={basename}>
      {isDemoMode && <DemoNav />}
      <Routes>
        {/* Public funnel pages (no auth) */}
        <Route path="/find" element={<FindBusiness />} />
        <Route path="/preview" element={<MerchantPreview />} />

        {/* Onboarding Flow */}
        <Route path="/claim" element={<ClaimBusiness />} />
        <Route path="/claim/:merchantId" element={<ClaimBusiness />} />
        <Route path="/claim/verify" element={<ClaimVerify />} />
        <Route path="/claim/location" element={<SelectLocation />} />

        {/* Staff-Facing Customer View */}
        <Route path="/exclusive/:exclusiveId" element={<CustomerExclusiveView />} />

        {/* Main Dashboard */}
        <Route path="/" element={isClaimed ? <DashboardLayout /> : <Navigate to="/claim" replace />}>
          <Route index element={<Overview />} />
          <Route path="overview" element={<Overview />} />
          <Route path="exclusives" element={<Exclusives />} />
          <Route path="exclusives/new" element={<CreateExclusive />} />
          <Route path="visits" element={<Visits />} />
          <Route path="ev-arrivals" element={<EVArrivals />} />
          <Route path="primary-experience" element={<PrimaryExperience />} />
          <Route path="pickup-packages" element={<PickupPackages />} />
          <Route path="pickup-packages/new" element={<CreatePickupPackage />} />
          <Route path="billing" element={<Billing />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
      <ConsentBanner />
    </BrowserRouter>
  );
}