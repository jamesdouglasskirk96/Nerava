import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { Merchants } from './components/Merchants';
import { ChargingLocations } from './components/ChargingLocations';
import { ActiveSessions } from './components/ActiveSessions';
import { Exclusives } from './components/Exclusives';
import { Overrides } from './components/Overrides';
import { Logs } from './components/Logs';

export default function App() {
  const [activeScreen, setActiveScreen] = useState('dashboard');

  const renderScreen = () => {
    switch (activeScreen) {
      case 'dashboard':
        return <Dashboard />;
      case 'merchants':
        return <Merchants />;
      case 'charging-locations':
        return <ChargingLocations />;
      case 'active-sessions':
        return <ActiveSessions />;
      case 'exclusives':
        return <Exclusives />;
      case 'overrides':
        return <Overrides />;
      case 'logs':
        return <Logs />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-neutral-50">
      <Sidebar activeScreen={activeScreen} setActiveScreen={setActiveScreen} />
      <main className="flex-1 overflow-auto">
        {renderScreen()}
      </main>
    </div>
  );
}
