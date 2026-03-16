import { Outlet, NavLink } from 'react-router-dom';
import { LayoutDashboard, Sparkles, Megaphone, Package, CreditCard, Settings, Users, LogOut, Car, BarChart3, Heart } from 'lucide-react';
import { logout, fetchMyMerchant } from '../services/api';
import { useEffect, useState } from 'react';

export function DashboardLayout() {
  const [merchantName, setMerchantName] = useState(localStorage.getItem('merchant_name') || '');

  // Resolve merchant_id on mount and check token expiry
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp;
        if (exp && Date.now() >= exp * 1000) {
          logout();
          return;
        }
      } catch {
        logout();
        return;
      }
    }

    // Fetch merchant profile to get merchant_id if not already set
    if (!localStorage.getItem('merchant_id')) {
      fetchMyMerchant()
        .then((data) => {
          if (data.merchant?.id) {
            localStorage.setItem('merchant_id', data.merchant.id);
            if (data.merchant.name) {
              localStorage.setItem('merchant_name', data.merchant.name);
              setMerchantName(data.merchant.name);
            }
          }
        })
        .catch(() => {
          // Merchant not found — may need to complete claim flow
        });
    }
  }, []);

  const handleLogout = () => {
    logout();
  };

  const navItems = [
    { to: '/overview', label: 'Overview', icon: LayoutDashboard },
    { to: '/exclusives', label: 'Exclusives', icon: Sparkles },
    { to: '/ev-arrivals', label: 'EV Arrivals', icon: Car },
    { to: '/visits', label: 'Visits', icon: Users },
    { to: '/loyalty', label: 'Loyalty', icon: Heart },
    { to: '/insights', label: 'Insights', icon: BarChart3 },
    { to: '/nerava-ads', label: 'Nerava Ads', icon: Megaphone },
    { to: '/pickup-packages', label: 'Pickup Packages', icon: Package },
    { to: '/billing', label: 'Billing', icon: CreditCard },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-neutral-50 flex">
      {/* Left Sidebar */}
      <aside className="w-64 bg-white border-r border-neutral-200 fixed h-full flex flex-col">
        <div className="p-6 border-b border-neutral-200">
          <h1 className="text-xl text-neutral-900">{merchantName || 'Nerava'}</h1>
          <p className="text-sm text-neutral-500 mt-1">Merchant Portal</p>
        </div>
        
        <nav className="p-4 flex-1">
          <ul className="space-y-1">
            {navItems.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-neutral-900 text-white'
                        : 'text-neutral-600 hover:bg-neutral-100'
                    }`
                  }
                >
                  <item.icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {/* Logout Button */}
        <div className="p-4 border-t border-neutral-200">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-neutral-600 hover:bg-neutral-100 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-64 flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
