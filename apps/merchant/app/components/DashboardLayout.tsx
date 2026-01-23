import { Outlet, NavLink } from 'react-router-dom';
import { LayoutDashboard, Sparkles, Star, Package, CreditCard, Settings, Users } from 'lucide-react';

export function DashboardLayout() {
  const navItems = [
    { to: '/overview', label: 'Overview', icon: LayoutDashboard },
    { to: '/exclusives', label: 'Exclusives', icon: Sparkles },
    { to: '/visits', label: 'Visits', icon: Users },
    { to: '/primary-experience', label: 'Primary Experience', icon: Star },
    { to: '/pickup-packages', label: 'Pickup Packages', icon: Package },
    { to: '/billing', label: 'Billing', icon: CreditCard },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-neutral-50 flex">
      {/* Left Sidebar */}
      <aside className="w-64 bg-white border-r border-neutral-200 fixed h-full">
        <div className="p-6 border-b border-neutral-200">
          <h1 className="text-xl text-neutral-900">Nerava</h1>
          <p className="text-sm text-neutral-500 mt-1">Merchant Portal</p>
        </div>
        
        <nav className="p-4">
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
