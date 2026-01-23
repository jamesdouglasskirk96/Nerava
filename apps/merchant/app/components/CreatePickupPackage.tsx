import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Info } from 'lucide-react';

export function CreatePickupPackage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    startTime: '09:00',
    endTime: '17:00',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/pickup-packages');
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div>
      <button
        onClick={() => navigate('/pickup-packages')}
        className="flex items-center gap-2 text-neutral-600 hover:text-neutral-900 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Pickup Packages
      </button>

      <div className="mb-8">
        <h1 className="text-3xl text-neutral-900 mb-2">Create Pickup Package</h1>
        <p className="text-neutral-600">
          Design a pre-order package for charging customers
        </p>
      </div>

      <div className="max-w-3xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-white p-6 rounded-lg border border-neutral-200">
            <label className="block">
              <span className="text-sm text-neutral-900">Package Name</span>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="e.g., Coffee & Pastry Bundle"
                className="mt-1 w-full px-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                required
              />
            </label>
          </div>

          <div className="bg-white p-6 rounded-lg border border-neutral-200">
            <label className="block">
              <span className="text-sm text-neutral-900">Description</span>
              <textarea
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                placeholder="What's included in this package?"
                rows={3}
                className="mt-1 w-full px-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent resize-none"
                required
              />
            </label>
          </div>

          <div className="bg-white p-6 rounded-lg border border-neutral-200">
            <label className="block">
              <span className="text-sm text-neutral-900">Price</span>
              <div className="relative mt-1">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500">$</span>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.price}
                  onChange={(e) => handleChange('price', e.target.value)}
                  placeholder="0.00"
                  className="w-full pl-8 pr-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                  required
                />
              </div>
            </label>
          </div>

          <div className="bg-white p-6 rounded-lg border border-neutral-200">
            <div className="mb-3">
              <span className="text-sm text-neutral-900">Available Time Window</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <label className="block">
                <span className="text-xs text-neutral-600">Start Time</span>
                <input
                  type="time"
                  value={formData.startTime}
                  onChange={(e) => handleChange('startTime', e.target.value)}
                  className="mt-1 w-full px-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                  required
                />
              </label>
              <label className="block">
                <span className="text-xs text-neutral-600">End Time</span>
                <input
                  type="time"
                  value={formData.endTime}
                  onChange={(e) => handleChange('endTime', e.target.value)}
                  className="mt-1 w-full px-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                  required
                />
              </label>
            </div>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-start gap-2">
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-sm text-blue-900 mb-1">Payment Processing</div>
                <div className="text-xs text-blue-700">
                  Customers pay through Nerava. Funds are transferred to your account weekly, minus processing fees.
                </div>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => navigate('/pickup-packages')}
              className="flex-1 border border-neutral-300 text-neutral-700 py-3 px-6 rounded-lg hover:bg-neutral-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 bg-neutral-900 text-white py-3 px-6 rounded-lg hover:bg-neutral-800 transition-colors"
            >
              Create Package
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
