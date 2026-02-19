import { Star, CheckCircle, AlertCircle, Info } from 'lucide-react';

import { useState } from 'react';

type PrimaryStatus = 'available' | 'active' | 'taken';

const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';

export function PrimaryExperience() {
  // Mock status - can be 'available', 'active', or 'taken' (only in demo mode)
  const [status] = useState<PrimaryStatus>(isDemoMode ? 'available' : 'available');
  const currentHolder = isDemoMode ? 'Downtown Cafe' : null; // Only relevant if status is 'taken'

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl text-neutral-900 mb-2">Primary Experience</h1>
        <p className="text-neutral-600">
          Maximize your visibility at charging locations
        </p>
      </div>

      {/* Explanation Card */}
      <div className="bg-gradient-to-br from-amber-50 to-amber-100 p-8 rounded-xl border border-amber-200 mb-8">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-white rounded-lg shadow-sm">
            <Star className="w-8 h-8 text-amber-600" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl text-neutral-900 mb-3">What is Primary Experience?</h2>
            <p className="text-neutral-700 mb-4">
              Each charging location supports one Primary Experience. This gives you:
            </p>
            <ul className="space-y-2 text-neutral-700">
              <li className="flex items-start gap-2">
                <CheckCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <span><strong>Maximum visibility</strong> – Your exclusive appears first to all charging customers</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <span><strong>Featured placement</strong> – Highlighted in the customer's charging window</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <span><strong>Exclusive scarcity</strong> – Only one business per location can hold this position</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Status Card - Available */}
      {status === 'available' && (
        <div className="bg-white p-8 rounded-lg border border-neutral-200">
          <div className="text-center max-w-2xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-full text-sm mb-6">
              <CheckCircle className="w-4 h-4" />
              Available Now
            </div>
            
            <h2 className="text-2xl text-neutral-900 mb-3">
              Primary Experience is Available
            </h2>
            <p className="text-neutral-600 mb-8">
              Reserve the Primary Experience slot at your charging location. You'll be the only business with this premium placement.
            </p>

            <div className="grid grid-cols-3 gap-6 mb-8 text-left">
              <div className="p-4 bg-neutral-50 rounded-lg">
                <div className="text-2xl text-neutral-900 mb-1">$99</div>
                <div className="text-sm text-neutral-600">per month</div>
              </div>
              <div className="p-4 bg-neutral-50 rounded-lg">
                <div className="text-2xl text-neutral-900 mb-1">30 days</div>
                <div className="text-sm text-neutral-600">minimum commitment</div>
              </div>
              <div className="p-4 bg-neutral-50 rounded-lg">
                <div className="text-2xl text-neutral-900 mb-1">Cancel</div>
                <div className="text-sm text-neutral-600">anytime after 30 days</div>
              </div>
            </div>

            {isDemoMode ? (
              <button className="bg-neutral-900 text-white px-8 py-4 rounded-lg hover:bg-neutral-800 transition-colors text-lg">
                Reserve Primary Experience
              </button>
            ) : (
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <p className="text-blue-900 text-sm">Coming Soon</p>
                <p className="text-blue-700 text-xs mt-1">Primary Experience reservation will be available soon</p>
              </div>
            )}

            <div className="mt-6 p-4 bg-blue-50 rounded-lg text-left">
              <div className="flex items-start gap-2">
                <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-900">
                  Your Primary Experience will activate immediately upon payment confirmation.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Status Card - Active */}
      {status === 'active' && (
        <div className="bg-white p-8 rounded-lg border border-neutral-200">
          <div className="text-center max-w-2xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-full text-sm mb-6">
              <CheckCircle className="w-4 h-4" />
              Active
            </div>
            
            <h2 className="text-2xl text-neutral-900 mb-3">
              You are the Primary Experience
            </h2>
            <p className="text-neutral-600 mb-8">
              Your exclusive has maximum visibility to all charging customers at this location.
            </p>

            <div className="grid grid-cols-2 gap-6 mb-8">
              <div className="p-6 bg-neutral-50 rounded-lg text-left">
                <div className="text-sm text-neutral-600 mb-1">Next Billing Date</div>
                <div className="text-xl text-neutral-900">February 5, 2026</div>
              </div>
              <div className="p-6 bg-neutral-50 rounded-lg text-left">
                <div className="text-sm text-neutral-600 mb-1">Monthly Rate</div>
                <div className="text-xl text-neutral-900">$99.00</div>
              </div>
            </div>

            {isDemoMode ? (
              <div className="flex gap-3">
                <button className="flex-1 border border-neutral-300 text-neutral-700 py-3 px-6 rounded-lg hover:bg-neutral-50 transition-colors">
                  View Details
                </button>
                <button className="flex-1 border border-red-300 text-red-700 py-3 px-6 rounded-lg hover:bg-red-50 transition-colors">
                  Cancel Primary
                </button>
              </div>
            ) : (
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <p className="text-blue-900 text-sm">Coming Soon</p>
                <p className="text-blue-700 text-xs mt-1">Primary Experience management will be available soon</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Status Card - Taken */}
      {status === 'taken' && (
        <div className="bg-white p-8 rounded-lg border border-neutral-200">
          <div className="text-center max-w-2xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-100 text-amber-700 rounded-full text-sm mb-6">
              <AlertCircle className="w-4 h-4" />
              Currently Taken
            </div>
            
            <h2 className="text-2xl text-neutral-900 mb-3">
              Primary Experience is Taken
            </h2>
            <p className="text-neutral-600 mb-8">
              Another business (<strong>{currentHolder}</strong>) currently holds the Primary Experience at this location.
            </p>

            {isDemoMode ? (
              <div className="p-6 bg-neutral-50 rounded-lg mb-8">
                <h3 className="text-lg text-neutral-900 mb-3">Join the Waitlist</h3>
                <p className="text-sm text-neutral-600 mb-4">
                  We'll notify you immediately if the Primary Experience becomes available. You'll have priority access to claim it.
                </p>
                <button className="bg-neutral-900 text-white px-6 py-3 rounded-lg hover:bg-neutral-800 transition-colors">
                  Join Waitlist
                </button>
              </div>
            ) : (
              <div className="p-6 bg-neutral-50 rounded-lg mb-8 text-center">
                <p className="text-neutral-600">Coming Soon</p>
                <p className="text-sm text-neutral-500 mt-2">Waitlist functionality will be available soon</p>
              </div>
            )}

            <div className="p-4 bg-blue-50 rounded-lg text-left">
              <div className="flex items-start gap-2">
                <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-900">
                  You can still create regular exclusives while on the waitlist. They'll appear below the Primary Experience.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
