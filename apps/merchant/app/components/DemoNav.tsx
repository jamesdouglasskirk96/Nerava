import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ChevronDown, X, Eye } from 'lucide-react';

export function DemoNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(true);

  interface FlowItem {
    name: string;
    path: string;
    requiresClaim?: boolean;
  }

  interface Flow {
    label: string;
    items: FlowItem[];
  }

  const flows: Flow[] = [
    {
      label: 'FLOW A - Onboarding',
      items: [
        { name: 'Claim Business', path: '/claim' },
        { name: 'Select Location', path: '/claim/location' },
      ],
    },
    {
      label: 'FLOW B - Dashboard',
      items: [
        { name: 'Overview (Home)', path: '/overview', requiresClaim: true },
        { name: 'Exclusives', path: '/exclusives', requiresClaim: true },
        { name: 'Create Exclusive', path: '/exclusives/new', requiresClaim: true },
        { name: 'Primary Experience', path: '/primary-experience', requiresClaim: true },
        { name: 'Pickup Packages', path: '/pickup-packages', requiresClaim: true },
        { name: 'Create Pickup Package', path: '/pickup-packages/new', requiresClaim: true },
        { name: 'Billing', path: '/billing', requiresClaim: true },
        { name: 'Settings', path: '/settings', requiresClaim: true },
      ],
    },
    {
      label: 'FLOW G - Staff View',
      items: [
        { name: 'Customer Exclusive Screen', path: '/exclusive/1' },
      ],
    },
  ];

  const handleNavigate = (path: string, requiresClaim?: boolean) => {
    if (requiresClaim) {
      localStorage.setItem('businessClaimed', 'true');
    }
    navigate(path);
    setIsOpen(false);
  };

  const resetDemo = () => {
    localStorage.removeItem('businessClaimed');
    navigate('/claim');
    setIsOpen(false);
  };

  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      {/* Collapsed Bar */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="w-full bg-purple-600 text-white py-2 px-4 flex items-center justify-center gap-2 hover:bg-purple-700 transition-colors text-sm"
        >
          <Eye className="w-4 h-4" />
          Demo Navigation - Click to View All Flows
          <ChevronDown className="w-4 h-4" />
        </button>
      )}

      {/* Expanded Panel */}
      {isOpen && (
        <div className="bg-purple-600 text-white shadow-lg max-h-screen overflow-y-auto">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Eye className="w-5 h-5" />
                <span className="font-semibold">Demo Navigation</span>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={resetDemo}
                  className="text-xs bg-purple-700 px-3 py-1 rounded hover:bg-purple-800 transition-colors"
                >
                  Reset Demo
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-purple-700 rounded transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              {flows.map((flow, idx) => (
                <div key={idx} className="bg-purple-700 rounded-lg p-3">
                  <div className="text-xs font-semibold mb-2 text-purple-200 uppercase">
                    {flow.label}
                  </div>
                  <div className="space-y-1">
                    {flow.items.map((item, itemIdx) => (
                      <button
                        key={itemIdx}
                        onClick={() => handleNavigate(item.path, item.requiresClaim)}
                        type="button"
                        className={`w-full text-left text-sm px-3 py-2 rounded transition-colors cursor-pointer ${
                          location.pathname === item.path
                            ? 'bg-purple-900 text-white font-medium'
                            : 'hover:bg-purple-600 text-purple-100 hover:text-white'
                        }`}
                      >
                        {item.name}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-3 text-xs text-purple-200 text-center">
              Current: {location.pathname} | Business Claimed: {localStorage.getItem('businessClaimed') || 'false'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}