import { MapPin, CheckCircle, XCircle } from 'lucide-react';

interface ChargingLocation {
  id: string;
  name: string;
  address: string;
  associatedMerchants: string[];
  primaryExperienceStatus: 'enabled' | 'disabled';
  liveSessionsCount: number;
  totalChargers: number;
}

const mockLocations: ChargingLocation[] = [
  {
    id: 'L001',
    name: 'Downtown Station #1',
    address: '1234 Pike St, Seattle, WA 98101',
    associatedMerchants: ['Voltage Coffee Bar', 'Current Cafe'],
    primaryExperienceStatus: 'enabled',
    liveSessionsCount: 12,
    totalChargers: 8,
  },
  {
    id: 'L002',
    name: 'Midtown Plaza',
    address: '567 Broadway, Portland, OR 97201',
    associatedMerchants: ['Peak Hours Gym'],
    primaryExperienceStatus: 'enabled',
    liveSessionsCount: 8,
    totalChargers: 6,
  },
  {
    id: 'L003',
    name: 'Capitol Hill Station',
    address: '890 Broadway E, Seattle, WA 98102',
    associatedMerchants: ['Bolt Bistro', 'EV Lounge'],
    primaryExperienceStatus: 'disabled',
    liveSessionsCount: 0,
    totalChargers: 10,
  },
  {
    id: 'L004',
    name: 'Downtown Station #4',
    address: '234 Union St, Seattle, WA 98101',
    associatedMerchants: ['Charge & Dine'],
    primaryExperienceStatus: 'enabled',
    liveSessionsCount: 6,
    totalChargers: 4,
  },
  {
    id: 'L005',
    name: 'Bellevue Center',
    address: '456 Bellevue Way, Bellevue, WA 98004',
    associatedMerchants: ['FastCharge Premium'],
    primaryExperienceStatus: 'enabled',
    liveSessionsCount: 3,
    totalChargers: 12,
  },
  {
    id: 'L006',
    name: 'Pearl District Hub',
    address: '789 NW 10th Ave, Portland, OR 97209',
    associatedMerchants: ['Current Cafe', 'Power Station Cafe'],
    primaryExperienceStatus: 'enabled',
    liveSessionsCount: 15,
    totalChargers: 8,
  },
];

export function ChargingLocations() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl text-neutral-900">Charging Locations</h1>
        <p className="text-sm text-neutral-600 mt-1">Monitor charging infrastructure and associations</p>
      </div>

      {/* Locations Grid */}
      <div className="grid grid-cols-1 gap-4">
        {mockLocations.map((location) => (
          <div key={location.id} className="bg-white border border-neutral-200 rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start gap-3">
                <div className="p-2.5 bg-blue-50 rounded-lg">
                  <MapPin className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg text-neutral-900">{location.name}</h3>
                  <p className="text-sm text-neutral-600 mt-0.5">{location.address}</p>
                  <div className="text-xs text-neutral-500 mt-1">ID: {location.id}</div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {location.primaryExperienceStatus === 'enabled' ? (
                  <div className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 border border-green-200 rounded-md">
                    <CheckCircle className="w-3.5 h-3.5 text-green-600" />
                    <span className="text-xs text-green-700">Primary Experience Active</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 px-3 py-1.5 bg-neutral-100 border border-neutral-300 rounded-md">
                    <XCircle className="w-3.5 h-3.5 text-neutral-600" />
                    <span className="text-xs text-neutral-700">Primary Experience Disabled</span>
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-4 gap-6 pt-4 border-t border-neutral-100">
              <div>
                <div className="text-xs text-neutral-600 mb-1">Associated Merchants</div>
                <div className="text-sm text-neutral-900">
                  {location.associatedMerchants.length > 0 ? (
                    <div className="space-y-0.5">
                      {location.associatedMerchants.map((merchant, idx) => (
                        <div key={idx} className="text-sm text-neutral-900">
                          {merchant}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-neutral-500">None</span>
                  )}
                </div>
              </div>

              <div>
                <div className="text-xs text-neutral-600 mb-1">Live Sessions</div>
                <div className="text-2xl text-neutral-900">{location.liveSessionsCount}</div>
              </div>

              <div>
                <div className="text-xs text-neutral-600 mb-1">Total Chargers</div>
                <div className="text-2xl text-neutral-900">{location.totalChargers}</div>
              </div>

              <div className="flex items-end justify-end">
                <button className="px-4 py-2 bg-neutral-900 text-white text-sm rounded-lg hover:bg-neutral-800">
                  View Details
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
