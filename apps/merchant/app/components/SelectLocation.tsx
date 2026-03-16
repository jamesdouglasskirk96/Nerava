import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, CheckCircle2, Loader2, Search } from 'lucide-react';
import { listGBPLocations, claimLocation, searchPlaces } from '../services/api';

interface LocationResult {
  place_id: string;
  name: string;
  address: string;
}

export function SelectLocation() {
  const navigate = useNavigate();
  const [locations, setLocations] = useState<LocationResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Try GBP locations first, fall back to search mode
  useEffect(() => {
    listGBPLocations()
      .then((data) => {
        const locs = data.locations || [];
        if (locs.length > 0) {
          setLocations(locs);
        } else {
          setShowSearch(true);
        }
      })
      .catch(() => {
        // GBP not available — show search instead
        setShowSearch(true);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (query.length < 3) {
      setLocations([]);
      return;
    }
    searchTimeout.current = setTimeout(async () => {
      setSearching(true);
      try {
        const results = await searchPlaces(query);
        setLocations(
          results.map((r) => ({
            place_id: r.place_id,
            name: r.name,
            address: r.address || '',
          }))
        );
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Search failed');
      } finally {
        setSearching(false);
      }
    }, 400);
  };

  const handleConfirm = async () => {
    if (!selectedLocation) return;

    const loc = locations.find((l) => l.place_id === selectedLocation);
    if (!loc) return;

    setClaiming(true);
    setError(null);
    try {
      await claimLocation(loc.place_id, loc.name, loc.address);
      localStorage.setItem('businessClaimed', 'true');
      localStorage.setItem('place_id', loc.place_id);
      localStorage.setItem('merchant_name', loc.name);
      navigate('/overview');
    } catch (err: any) {
      setError(err.message || 'Failed to claim location');
    } finally {
      setClaiming(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-neutral-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-white rounded-xl shadow-sm border border-neutral-200 p-8">
        <div className="mb-8">
          <h1 className="text-3xl text-neutral-900 mb-2">
            {showSearch ? 'Find Your Business' : 'Select Your Location'}
          </h1>
          <p className="text-neutral-600">
            {showSearch
              ? 'Search for your business to claim it on Nerava'
              : 'Choose the business location you\'d like to manage on Nerava'}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {showSearch && (
          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search for your business name..."
              className="w-full pl-10 pr-4 py-3 border border-neutral-300 rounded-lg text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
              autoFocus
            />
            {searching && (
              <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 animate-spin text-neutral-400" />
            )}
          </div>
        )}

        {showSearch && searchQuery.length < 3 && locations.length === 0 && (
          <div className="text-center py-8 text-neutral-500 text-sm">
            Type at least 3 characters to search
          </div>
        )}

        {showSearch && searchQuery.length >= 3 && !searching && locations.length === 0 && (
          <div className="text-center py-8 text-neutral-500 text-sm">
            No businesses found. Try a different search.
          </div>
        )}

        <div className="space-y-3 mb-8 max-h-96 overflow-y-auto">
          {locations.map((location) => (
            <button
              key={location.place_id}
              onClick={() => setSelectedLocation(location.place_id)}
              className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                selectedLocation === location.place_id
                  ? 'border-neutral-900 bg-neutral-50'
                  : 'border-neutral-200 hover:border-neutral-300'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg text-neutral-900 mb-2">{location.name}</h3>
                  <div className="flex items-start gap-2 text-sm text-neutral-600">
                    <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>{location.address}</span>
                  </div>
                </div>
                {selectedLocation === location.place_id && (
                  <CheckCircle2 className="w-6 h-6 text-neutral-900 flex-shrink-0" />
                )}
              </div>
            </button>
          ))}
        </div>

        {(locations.length > 0 || !showSearch) && (
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/claim')}
              className="flex-1 border border-neutral-300 text-neutral-700 py-3 px-6 rounded-lg hover:bg-neutral-50 transition-colors"
            >
              Back
            </button>
            <button
              onClick={handleConfirm}
              disabled={!selectedLocation || claiming}
              className="flex-1 bg-neutral-900 text-white py-3 px-6 rounded-lg hover:bg-neutral-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {claiming ? 'Claiming...' : 'Confirm Location'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
