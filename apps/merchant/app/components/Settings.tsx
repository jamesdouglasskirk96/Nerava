import { Building2, Clock, Bell, Mail, Info } from 'lucide-react';

// Mock business data
const businessInfo = {
  name: 'Downtown Coffee Shop',
  address: '123 Main St, San Francisco, CA 94102',
  hours: 'Mon-Fri: 7am-7pm, Sat-Sun: 8am-6pm',
};

const contactEmail = 'owner@downtowncoffee.com';

export function Settings() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl text-neutral-900 mb-2">Settings</h1>
        <p className="text-neutral-600">
          Manage your business information and preferences
        </p>
      </div>

      {/* Business Information */}
      <div className="mb-8">
        <h2 className="text-lg text-neutral-900 mb-4">Business Information</h2>
        <div className="bg-white p-6 rounded-lg border border-neutral-200 space-y-6">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-neutral-100 rounded-lg">
              <Building2 className="w-5 h-5 text-neutral-700" />
            </div>
            <div className="flex-1">
              <div className="text-sm text-neutral-600 mb-1">Business Name</div>
              <div className="text-lg text-neutral-900">{businessInfo.name}</div>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="p-2 bg-neutral-100 rounded-lg">
              <Building2 className="w-5 h-5 text-neutral-700" />
            </div>
            <div className="flex-1">
              <div className="text-sm text-neutral-600 mb-1">Address</div>
              <div className="text-lg text-neutral-900">{businessInfo.address}</div>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="p-2 bg-neutral-100 rounded-lg">
              <Clock className="w-5 h-5 text-neutral-700" />
            </div>
            <div className="flex-1">
              <div className="text-sm text-neutral-600 mb-1">Business Hours</div>
              <div className="text-lg text-neutral-900">{businessInfo.hours}</div>
              <div className="mt-2 flex items-start gap-2">
                <Info className="w-4 h-4 text-neutral-500 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-neutral-600">
                  Hours are synced from your Google Business Profile (read-only)
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Contact Email */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg text-neutral-900">Contact Email</h2>
          <button className="text-sm text-neutral-600 hover:text-neutral-900 transition-colors">
            Edit
          </button>
        </div>
        
        <div className="bg-white p-6 rounded-lg border border-neutral-200">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-neutral-100 rounded-lg">
              <Mail className="w-5 h-5 text-neutral-700" />
            </div>
            <div className="flex-1">
              <div className="text-sm text-neutral-600 mb-1">Primary Contact</div>
              <div className="text-lg text-neutral-900">{contactEmail}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Notification Preferences */}
      <div>
        <h2 className="text-lg text-neutral-900 mb-4">Notification Preferences</h2>
        <div className="bg-white rounded-lg border border-neutral-200 divide-y divide-neutral-200">
          <label className="p-6 flex items-center justify-between cursor-pointer hover:bg-neutral-50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-neutral-100 rounded-lg">
                <Bell className="w-5 h-5 text-neutral-700" />
              </div>
              <div>
                <div className="text-sm text-neutral-900 mb-1">Daily Summary</div>
                <div className="text-xs text-neutral-600">
                  Receive a daily email with activations and visit statistics
                </div>
              </div>
            </div>
            <input
              type="checkbox"
              defaultChecked
              className="w-5 h-5 rounded border-neutral-300 text-neutral-900 focus:ring-neutral-900"
            />
          </label>

          <label className="p-6 flex items-center justify-between cursor-pointer hover:bg-neutral-50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-neutral-100 rounded-lg">
                <Bell className="w-5 h-5 text-neutral-700" />
              </div>
              <div>
                <div className="text-sm text-neutral-900 mb-1">Cap Warnings</div>
                <div className="text-xs text-neutral-600">
                  Get notified when exclusives are approaching their daily cap
                </div>
              </div>
            </div>
            <input
              type="checkbox"
              defaultChecked
              className="w-5 h-5 rounded border-neutral-300 text-neutral-900 focus:ring-neutral-900"
            />
          </label>

          <label className="p-6 flex items-center justify-between cursor-pointer hover:bg-neutral-50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-neutral-100 rounded-lg">
                <Bell className="w-5 h-5 text-neutral-700" />
              </div>
              <div>
                <div className="text-sm text-neutral-900 mb-1">Billing Reminders</div>
                <div className="text-xs text-neutral-600">
                  Reminders about upcoming charges and payment issues
                </div>
              </div>
            </div>
            <input
              type="checkbox"
              defaultChecked
              className="w-5 h-5 rounded border-neutral-300 text-neutral-900 focus:ring-neutral-900"
            />
          </label>

          <label className="p-6 flex items-center justify-between cursor-pointer hover:bg-neutral-50 transition-colors">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-neutral-100 rounded-lg">
                <Bell className="w-5 h-5 text-neutral-700" />
              </div>
              <div>
                <div className="text-sm text-neutral-900 mb-1">Marketing Updates</div>
                <div className="text-xs text-neutral-600">
                  News about new features and best practices
                </div>
              </div>
            </div>
            <input
              type="checkbox"
              className="w-5 h-5 rounded border-neutral-300 text-neutral-900 focus:ring-neutral-900"
            />
          </label>
        </div>
      </div>
    </div>
  );
}
