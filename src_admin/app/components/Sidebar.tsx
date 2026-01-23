import { LayoutDashboard, Store, MapPin, Activity, Star, ShieldAlert, FileText } from 'lucide-react';

interface SidebarProps {
  activeScreen: string;
  setActiveScreen: (screen: string) => void;
}

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'merchants', label: 'Merchants', icon: Store },
  { id: 'charging-locations', label: 'Charging Locations', icon: MapPin },
  { id: 'active-sessions', label: 'Active Sessions', icon: Activity },
  { id: 'exclusives', label: 'Exclusives', icon: Star },
  { id: 'overrides', label: 'Overrides', icon: ShieldAlert },
  { id: 'logs', label: 'Logs', icon: FileText },
];

export function Sidebar({ activeScreen, setActiveScreen }: SidebarProps) {
  return (
    <aside className="w-64 bg-neutral-900 text-neutral-100 flex flex-col">
      <div className="p-6 border-b border-neutral-800">
        <h1 className="text-lg tracking-tight">Nerava Admin</h1>
        <p className="text-xs text-neutral-400 mt-1">Control Plane</p>
      </div>
      
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeScreen === item.id;
            
            return (
              <li key={item.id}>
                <button
                  onClick={() => setActiveScreen(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors ${
                    isActive
                      ? 'bg-neutral-800 text-white'
                      : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
      
      <div className="p-4 border-t border-neutral-800">
        <div className="text-xs text-neutral-500">
          <div>Operator: admin@nerava.com</div>
          <div className="mt-1">Session: {new Date().toLocaleDateString()}</div>
        </div>
      </div>
    </aside>
  );
}
