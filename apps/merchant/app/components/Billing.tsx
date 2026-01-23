import { CreditCard, DollarSign, Calendar, Info, Link } from 'lucide-react';
import { Link as RouterLink } from 'react-router-dom';

// Mock billing data
const billingItems = [
  {
    id: '1',
    name: 'Primary Experience',
    description: 'Premium placement at charging location',
    amount: 99.00,
    frequency: 'monthly',
    nextBilling: 'February 5, 2026',
  },
  {
    id: '2',
    name: 'Pickup Package Activations',
    description: 'Commission on pickup orders (10%)',
    amount: 45.30,
    frequency: 'monthly',
    nextBilling: 'Billed monthly',
  },
];

const paymentMethod = {
  type: 'Visa',
  last4: '4242',
  expiry: '12/2027',
};

export function Billing() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl text-neutral-900 mb-2">Billing</h1>
        <p className="text-neutral-600">
          Manage your payment methods and billing details
        </p>
      </div>

      {/* Manual Invoicing Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-900 mb-1">Pilot Billing</h3>
        <p className="text-blue-800 text-sm">
          During the pilot period, invoices are issued based on your verified visits.
          Payments are handled separately by our team.
          View your <RouterLink to="/visits" className="underline font-medium inline-flex items-center gap-1"><Link className="w-3 h-3" />verified visits</RouterLink> to see billable events.
        </p>
      </div>

      {/* How Billing Works */}
      <div className="bg-blue-50 p-6 rounded-lg mb-8">
        <div className="flex items-start gap-3 mb-4">
          <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h2 className="text-lg text-blue-900 mb-2">How Billing Works</h2>
            <div className="text-sm text-blue-800 space-y-2">
              <p><strong>Primary Experience:</strong> Billed monthly on your subscription date</p>
              <p><strong>Paid Exclusives:</strong> No upfront cost. You control pricing and availability</p>
              <p><strong>Pickup Activations:</strong> 10% commission on successful pickups, billed monthly</p>
            </div>
          </div>
        </div>
      </div>

      {/* Current Charges */}
      <div className="mb-8">
        <h2 className="text-lg text-neutral-900 mb-4">Current Charges</h2>
        <div className="bg-white rounded-lg border border-neutral-200 divide-y divide-neutral-200">
          {billingItems.map((item) => (
            <div key={item.id} className="p-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-lg text-neutral-900 mb-1">{item.name}</h3>
                  <p className="text-sm text-neutral-600">{item.description}</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl text-neutral-900">${item.amount.toFixed(2)}</div>
                  <div className="text-sm text-neutral-600">{item.frequency}</div>
                </div>
              </div>
              
              <div className="flex items-center gap-2 text-sm text-neutral-600">
                <Calendar className="w-4 h-4" />
                <span>Next billing: {item.nextBilling}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Payment Method */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg text-neutral-900">Payment Method</h2>
          <button className="text-sm text-neutral-600 hover:text-neutral-900 transition-colors">
            Update
          </button>
        </div>
        
        <div className="bg-white p-6 rounded-lg border border-neutral-200">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-neutral-100 rounded-lg">
              <CreditCard className="w-6 h-6 text-neutral-700" />
            </div>
            <div>
              <div className="text-lg text-neutral-900 mb-1">
                {paymentMethod.type} ending in {paymentMethod.last4}
              </div>
              <div className="text-sm text-neutral-600">
                Expires {paymentMethod.expiry}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Billing History Placeholder */}
      <div>
        <h2 className="text-lg text-neutral-900 mb-4">Billing History</h2>
        <div className="bg-white p-12 rounded-lg border border-neutral-200 text-center">
          <div className="max-w-md mx-auto">
            <div className="p-4 bg-neutral-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
              <DollarSign className="w-8 h-8 text-neutral-400" />
            </div>
            <h3 className="text-xl text-neutral-900 mb-2">No Invoices Yet</h3>
            <p className="text-neutral-600">
              Your billing history will appear here once you have been charged
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
