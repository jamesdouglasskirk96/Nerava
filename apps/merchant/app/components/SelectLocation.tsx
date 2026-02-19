import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, Clock, CheckCircle2, AlertCircle } from 'lucide-react';

const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';

// Mock location data (only used in demo mode)
const mockLocations = isDemoMode ? [
  {
    id: '1',
    name: 'Downtown Coffee Shop',
    address: '123 Main St, San Francisco, CA 94102',
    hours: 'Mon-Fri: 7am-7pm, Sat-Sun: 8am-6pm',
    claimed: false,
  },
  {
    id: '2',
    name: 'Downtown Coffee Shop - 2nd Location',
    address: '456 Market St, San Francisco, CA 94105',
    hours: 'Mon-Fri: 6am-8pm, Sat-Sun: 7am-7pm',
    claimed: false,
  },
] : [];

export function SelectLocation() {
  const navigate = useNavigate();
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null);
  const [showAlreadyClaimed, setShowAlreadyClaimed] = useState(false);

  const handleConfirm = () => {
    if (selectedLocation) {
      localStorage.setItem('businessClaimed', 'true');
      localStorage.setItem('locationId', selectedLocation);
      navigate('/overview');
    }
  };

  const handleLocationClaimed = () => {
    setShowAlreadyClaimed(true);
  };

  if (showAlreadyClaimed) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-xl shadow-sm border border-neutral-200 p-8">
          <div className="text-center mb-6">
            <AlertCircle className="w-16 h-16 text-amber-500 mx-auto mb-4" />
            <h1 className="text-2xl text-neutral-900 mb-2">Location Already Claimed</h1>
            <p className="text-neutral-600">
              This location has already been claimed by another user.
            </p>
          </div>

          <div className="space-y-3">
            <button className="w-full bg-neutral-900 text-white py-3 px-6 rounded-lg hover:bg-neutral-800 transition-colors">
              Join Waitlist
            </button>
            <button className="w-full border border-neutral-300 text-neutral-700 py-3 px-6 rounded-lg hover:bg-neutral-50 transition-colors">
              Contact Support
            </button>
            <button
              onClick={() => setShowAlreadyClaimed(false)}
              className="w-full text-neutral-600 py-2 hover:text-neutral-900 transition-colors"
            >
              Back to Locations
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-white rounded-xl shadow-sm border border-neutral-200 p-8">
        <div className="mb-8">
          <h1 className="text-3xl text-neutral-900 mb-2">Select Your Location</h1>
          <p className="text-neutral-600">
            Choose the business location you'd like to manage
          </p>
        </div>

        {mockLocations.length === 0 && (
          <div className="text-center py-12">
            <AlertCircle className="w-16 h-16 text-neutral-400 mx-auto mb-4" />
            <h2 className="text-xl text-neutral-900 mb-2">No Locations Found</h2>
            <p className="text-neutral-600 mb-6">
              We couldn't find any business locations associated with your Google account.
            </p>
            <button className="bg-neutral-900 text-white py-3 px-6 rounded-lg hover:bg-neutral-800 transition-colors">
              Contact Support
            </button>
          </div>
        )}

        <div className="space-y-3 mb-8">
          {mockLocations.map((location) => (
            <button
              key={location.id}
              onClick={() => setSelectedLocation(location.id)}
              className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                selectedLocation === location.id
                  ? 'border-neutral-900 bg-neutral-50'
                  : 'border-neutral-200 hover:border-neutral-300'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg text-neutral-900 mb-2">{location.name}</h3>
                  
                  <div className="flex items-start gap-2 text-sm text-neutral-600 mb-2">
                    <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>{location.address}</span>
                  </div>
                  
                  <div className="flex items-start gap-2 text-sm text-neutral-600">
                    <Clock className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>{location.hours}</span>
                  </div>
                </div>
                
                {selectedLocation === location.id && (
                  <CheckCircle2 className="w-6 h-6 text-neutral-900 flex-shrink-0" />
                )}
              </div>
            </button>
          ))}
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => navigate('/claim')}
            className="flex-1 border border-neutral-300 text-neutral-700 py-3 px-6 rounded-lg hover:bg-neutral-50 transition-colors"
          >
            Back
          </button>
          <button
            onClick={handleConfirm}
            disabled={!selectedLocation}
            className="flex-1 bg-neutral-900 text-white py-3 px-6 rounded-lg hover:bg-neutral-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Confirm Location
          </button>
        </div>

        {isDemoMode && (
          <button
            onClick={handleLocationClaimed}
            className="mt-4 text-sm text-neutral-500 hover:text-neutral-700 w-full text-center"
          >
            Demo: Show "Already Claimed" State
          </button>
        )}
      </div>
    </div>
  );
}
