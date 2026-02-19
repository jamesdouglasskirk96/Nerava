import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Login } from './components/Login';
import { Dashboard } from './components/Dashboard';
import { Merchants } from './components/Merchants';
import { ChargingLocations } from './components/ChargingLocations';
import { ActiveSessions } from './components/ActiveSessions';
import { Exclusives } from './components/Exclusives';
import { Overrides } from './components/Overrides';
import { Deployments } from './components/Deployments';
import { Logs } from './components/Logs';
import { ConsentBanner } from './components/ConsentBanner';
import './App.css'

export default function App() {
  const [activeScreen, setActiveScreen] = useState('dashboard');
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('access_token'));

  useEffect(() => {
    // Check auth on mount
    setIsAuthenticated(!!localStorage.getItem('access_token'));
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('admin_email');
    setIsAuthenticated(false);
  };

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
      case 'deployments':
        return <Deployments />;
      case 'logs':
        return <Logs />;
      default:
        return <Dashboard />;
    }
  };

  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className="flex h-screen bg-neutral-50">
      <Sidebar activeScreen={activeScreen} setActiveScreen={setActiveScreen} onLogout={handleLogout} />
      <main className="flex-1 overflow-auto">
        {renderScreen()}
      </main>
      <ConsentBanner />
    </div>
  );
}
