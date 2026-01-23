import { useNavigate } from 'react-router-dom';
import { Plus, Clock, DollarSign, AlertCircle, Package } from 'lucide-react';

// Mock data
const mockPackages = [
  {
    id: '1',
    name: 'Coffee & Pastry Bundle',
    price: 12.99,
    description: 'Medium coffee and choice of pastry',
    timeWindow: '7:00 AM - 11:00 AM',
    ordersToday: 23,
    status: 'active',
  },
  {
    id: '2',
    name: 'Lunch Box Special',
    price: 15.99,
    description: 'Sandwich, chips, and drink',
    timeWindow: '11:00 AM - 2:00 PM',
    ordersToday: 18,
    status: 'active',
  },
];

export function PickupPackages() {
  const navigate = useNavigate();

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl text-neutral-900 mb-2">Pickup Packages</h1>
          <p className="text-neutral-600">
            Pre-order packages for charging customers to pickup
          </p>
        </div>
        <button
          onClick={() => navigate('/pickup-packages/new')}
          className="bg-neutral-900 text-white px-6 py-3 rounded-lg hover:bg-neutral-800 transition-colors flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Create Package
        </button>
      </div>

      <div className="bg-blue-50 p-4 rounded-lg mb-8">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900">
            <strong>Version 1:</strong> Simple predefined packages only. Custom orders and advanced features coming soon.
          </div>
        </div>
      </div>

      {mockPackages.length === 0 ? (
        <div className="bg-white rounded-lg border border-neutral-200 p-12 text-center">
          <div className="max-w-md mx-auto">
            <div className="p-4 bg-neutral-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <Package className="w-8 h-8 text-neutral-400" />
            </div>
            <h2 className="text-xl text-neutral-900 mb-2">No Pickup Packages Yet</h2>
            <p className="text-neutral-600 mb-6">
              Create your first pickup package for charging customers
            </p>
            <button
              onClick={() => navigate('/pickup-packages/new')}
              className="bg-neutral-900 text-white px-6 py-3 rounded-lg hover:bg-neutral-800 transition-colors inline-flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Create Package
            </button>
          </div>
        </div>
      ) : (
        <div className="grid gap-6">
          {mockPackages.map((pkg) => (
            <div key={pkg.id} className="bg-white p-6 rounded-lg border border-neutral-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl text-neutral-900">{pkg.name}</h3>
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      pkg.status === 'active' 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-neutral-100 text-neutral-600'
                    }`}>
                      {pkg.status === 'active' ? 'Active' : 'Paused'}
                    </span>
                  </div>
                  
                  <p className="text-sm text-neutral-600 mb-4">{pkg.description}</p>

                  <div className="flex items-center gap-6 text-sm">
                    <div className="flex items-center gap-2 text-neutral-600">
                      <DollarSign className="w-4 h-4" />
                      ${pkg.price.toFixed(2)}
                    </div>
                    <div className="flex items-center gap-2 text-neutral-600">
                      <Clock className="w-4 h-4" />
                      {pkg.timeWindow}
                    </div>
                    <div className="text-neutral-600">
                      {pkg.ordersToday} orders today
                    </div>
                  </div>
                </div>

                <button className="px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors">
                  Edit
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
