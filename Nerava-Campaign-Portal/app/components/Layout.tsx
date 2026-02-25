import { Outlet, Link, useLocation } from "react-router";
import {
  LayoutDashboard,
  Megaphone,
  MapPin,
  CreditCard,
  Settings,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", path: "/", icon: LayoutDashboard },
  { name: "Campaigns", path: "/campaigns", icon: Megaphone },
  { name: "Charger Explorer", path: "/charger-explorer", icon: MapPin },
  { name: "Billing", path: "/billing", icon: CreditCard },
  { name: "Settings", path: "/settings", icon: Settings },
];

export function Layout() {
  const location = useLocation();

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <aside className="w-64 bg-[#F7F8FA] border-r border-[#E4E6EB] flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-[#E4E6EB]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#1877F2] rounded flex items-center justify-center">
              <span className="text-white font-bold text-lg">N</span>
            </div>
            <span className="font-semibold text-[#050505]">Nerava</span>
          </div>
          <div className="text-xs text-[#65676B] mt-2">Acme Energy Corp</div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navigation.map((item) => {
            const isActive =
              location.pathname === item.path ||
              (item.path !== "/" && location.pathname.startsWith(item.path));

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center gap-3 px-3 py-2 rounded text-sm font-medium transition-colors
                  ${
                    isActive
                      ? "bg-white text-[#1877F2] shadow-sm"
                      : "text-[#65676B] hover:bg-white/50 hover:text-[#050505]"
                  }
                `}
              >
                <item.icon className="w-5 h-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
