import { useState, useEffect, useRef, useCallback } from "react";
import { MapPin, Plus, Loader2, Search, Zap, X } from "lucide-react";
import { Link } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { browseChargers, type BrowseCharger } from "../services/api";

const NETWORK_COLORS: Record<string, string> = {
  Tesla: "#CC0000",
  "Tesla Destination": "#E04040",
  "ChargePoint Network": "#FF6B00",
  "Electrify America": "#00A3E0",
  EVgo: "#00B140",
  "Blink Network": "#1A73E8",
  FLO: "#6B21A8",
  Volta: "#14B8A6",
};

function getNetworkColor(network: string | null): string {
  if (!network) return "#65676B";
  return NETWORK_COLORS[network] || "#65676B";
}

function createChargerIcon(network: string | null, selected: boolean, hasSessions: boolean) {
  const color = getNetworkColor(network);
  const size = selected ? 32 : 24;
  const opacity = hasSessions ? 1 : 0.7;
  const ring = hasSessions
    ? `<circle cx="12" cy="10" r="4.5" fill="none" stroke="#22C55E" stroke-width="1.5"/>`
    : "";
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="${color}" opacity="${opacity}" stroke="white" stroke-width="1.5"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="3" fill="white" stroke="none"/>${ring}</svg>`;
  return L.divIcon({
    html: svg,
    className: "",
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
  });
}

export function ChargerExplorer() {
  const [chargers, setChargers] = useState<BrowseCharger[]>([]);
  const [selectedCharger, setSelectedCharger] = useState<BrowseCharger | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [networkFilter, setNetworkFilter] = useState("");
  const [total, setTotal] = useState(0);
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const loadChargers = useCallback(async (search?: string, network?: string) => {
    try {
      setLoading(true);
      const { chargers: data, total: count } = await browseChargers({
        search: search || undefined,
        network: network || undefined,
        limit: 1000,
      });
      setChargers(data);
      setTotal(count);
      if (data.length > 0 && !selectedCharger) {
        setSelectedCharger(data[0]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load chargers");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadChargers();
  }, [loadChargers]);

  // Debounced search
  useEffect(() => {
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    searchTimeoutRef.current = setTimeout(() => {
      loadChargers(searchQuery, networkFilter);
    }, 300);
    return () => {
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    };
  }, [searchQuery, networkFilter, loadChargers]);

  // Initialize map
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;
    const map = L.map(mapRef.current, {
      center: [30.27, -97.74], // Austin, TX
      zoom: 10,
      zoomControl: true,
    });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "",
      maxZoom: 19,
    }).addTo(map);
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update markers when chargers change
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    const bounds: [number, number][] = [];

    chargers.forEach((charger) => {
      if (charger.lat == null || charger.lng == null) return;

      const marker = L.marker([charger.lat, charger.lng], {
        icon: createChargerIcon(
          charger.network_name,
          selectedCharger?.id === charger.id,
          charger.total_sessions > 0
        ),
      });

      const tooltipContent = `<strong>${charger.name}</strong>${
        charger.network_name ? `<br/>${charger.network_name}` : ""
      }${charger.total_sessions > 0 ? `<br/>${charger.total_sessions} sessions` : ""}`;

      marker.bindTooltip(tooltipContent, {
        direction: "top",
        offset: [0, -10],
        className: "text-xs",
      });

      marker.on("click", () => {
        setSelectedCharger(charger);
        // Pan to charger
        map.setView([charger.lat!, charger.lng!], Math.max(map.getZoom(), 14), {
          animate: true,
        });
      });

      marker.addTo(map);
      markersRef.current.push(marker);
      bounds.push([charger.lat, charger.lng]);
    });

    if (bounds.length > 0 && !selectedCharger) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
    }
  }, [chargers, selectedCharger]);

  // Update selected marker icon when selection changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    markersRef.current.forEach((marker, i) => {
      const charger = chargers.filter((c) => c.lat != null && c.lng != null)[i];
      if (!charger) return;
      marker.setIcon(
        createChargerIcon(
          charger.network_name,
          selectedCharger?.id === charger.id,
          charger.total_sessions > 0
        )
      );
    });
  }, [selectedCharger, chargers]);

  // Get unique networks for filter
  const networks = Array.from(
    new Set(chargers.map((c) => c.network_name).filter(Boolean))
  ).sort() as string[];

  function createCampaignUrl(charger: BrowseCharger): string {
    const params = new URLSearchParams();
    params.set("charger_id", charger.id);
    params.set("charger_name", charger.name);
    if (charger.network_name) params.set("network", charger.network_name);
    return `/campaigns/create?${params}`;
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-6 py-4 bg-white border-b border-[#E4E6EB] flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[#050505]">
            Charger Explorer
          </h1>
          <p className="text-sm text-[#65676B]">
            {total.toLocaleString()} chargers in database
          </p>
        </div>
        <Link
          to="/campaigns/create"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors rounded"
        >
          <Plus className="w-4 h-4" />
          New Campaign
        </Link>
      </div>

      <div className="flex-1 flex min-h-0">
        {/* Map Panel */}
        <div className="flex-1 relative">
          <div ref={mapRef} className="absolute inset-0" />

          {/* Search overlay */}
          <div className="absolute top-4 left-4 right-4 z-[1000] flex gap-2">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#65676B]" />
              <input
                type="text"
                placeholder="Search chargers by name, address, city, or network..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-8 py-2.5 bg-white border border-[#E4E6EB] shadow-lg text-sm rounded focus:outline-none focus:ring-2 focus:ring-[#1877F2]"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                >
                  <X className="w-3 h-3 text-[#65676B]" />
                </button>
              )}
            </div>
            <select
              value={networkFilter}
              onChange={(e) => setNetworkFilter(e.target.value)}
              className="bg-white border border-[#E4E6EB] shadow-lg text-sm py-2.5 px-3 rounded focus:outline-none focus:ring-2 focus:ring-[#1877F2]"
            >
              <option value="">All Networks</option>
              {networks.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>

          {/* Loading indicator */}
          {loading && (
            <div className="absolute top-20 left-1/2 -translate-x-1/2 z-[1000] bg-white border border-[#E4E6EB] shadow-lg px-4 py-2 rounded flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-[#1877F2]" />
              <span className="text-sm text-[#65676B]">Loading chargers...</span>
            </div>
          )}

          {/* Network legend */}
          <div className="absolute bottom-4 left-4 z-[1000] bg-white/95 border border-[#E4E6EB] p-3 shadow-lg rounded text-xs">
            <div className="font-semibold text-[#050505] mb-2">Networks</div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
              {Object.entries(NETWORK_COLORS).slice(0, 6).map(([name, color]) => (
                <div key={name} className="flex items-center gap-1.5">
                  <div
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-[#050505] truncate">{name}</span>
                </div>
              ))}
            </div>
            <div className="mt-1.5 pt-1.5 border-t border-[#E4E6EB] flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full border-2 border-green-500" />
              <span className="text-[#65676B]">Has session data</span>
            </div>
          </div>
        </div>

        {/* Detail Panel */}
        <div className="w-96 bg-white border-l border-[#E4E6EB] overflow-y-auto flex flex-col">
          {selectedCharger ? (
            <div className="p-6 border-b border-[#E4E6EB]">
              {/* Charger header */}
              <div className="mb-4">
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <h2 className="text-lg font-semibold text-[#050505] leading-tight">
                      {selectedCharger.name}
                    </h2>
                    {selectedCharger.network_name && (
                      <div className="flex items-center gap-1.5 mt-1">
                        <div
                          className="w-2 h-2 rounded-full"
                          style={{
                            backgroundColor: getNetworkColor(
                              selectedCharger.network_name
                            ),
                          }}
                        />
                        <span className="text-sm text-[#65676B]">
                          {selectedCharger.network_name}
                        </span>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setSelectedCharger(null)}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <X className="w-4 h-4 text-[#65676B]" />
                  </button>
                </div>
                {selectedCharger.address && (
                  <p className="text-xs text-[#65676B] mt-2">
                    {selectedCharger.address}
                    {selectedCharger.city && `, ${selectedCharger.city}`}
                    {selectedCharger.state && ` ${selectedCharger.state}`}
                  </p>
                )}
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                {selectedCharger.power_kw && (
                  <div className="p-3 bg-[#F7F8FA] border border-[#E4E6EB] rounded">
                    <div className="text-xs text-[#65676B]">Power</div>
                    <div className="text-base font-semibold text-[#050505]">
                      {selectedCharger.power_kw} kW
                    </div>
                  </div>
                )}
                {selectedCharger.num_evse && (
                  <div className="p-3 bg-[#F7F8FA] border border-[#E4E6EB] rounded">
                    <div className="text-xs text-[#65676B]">Stalls</div>
                    <div className="text-base font-semibold text-[#050505]">
                      {selectedCharger.num_evse}
                    </div>
                  </div>
                )}
                <div className="p-3 bg-[#F7F8FA] border border-[#E4E6EB] rounded">
                  <div className="text-xs text-[#65676B]">Sessions (30d)</div>
                  <div className="text-base font-semibold text-[#050505]">
                    {selectedCharger.total_sessions}
                  </div>
                </div>
                <div className="p-3 bg-[#F7F8FA] border border-[#E4E6EB] rounded">
                  <div className="text-xs text-[#65676B]">Unique Drivers</div>
                  <div className="text-base font-semibold text-[#050505]">
                    {selectedCharger.unique_drivers}
                  </div>
                </div>
              </div>

              {/* Connector types */}
              {selectedCharger.connector_types &&
                selectedCharger.connector_types.length > 0 && (
                  <div className="mb-4">
                    <div className="text-xs text-[#65676B] mb-1.5">
                      Connectors
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedCharger.connector_types.map((ct) => (
                        <span
                          key={ct}
                          className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded"
                        >
                          <Zap className="w-3 h-3" />
                          {ct}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

              {selectedCharger.pricing_per_kwh != null && (
                <div className="mb-4 text-xs text-[#65676B]">
                  Pricing: ${selectedCharger.pricing_per_kwh.toFixed(2)}/kWh
                </div>
              )}

              {/* Charger ID */}
              <div className="mb-4 text-xs text-[#65676B] font-mono">
                ID: {selectedCharger.id}
              </div>

              {/* Create Campaign button */}
              <Link
                to={createCampaignUrl(selectedCharger)}
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors rounded"
              >
                <Plus className="w-4 h-4" />
                Create Campaign for This Charger
              </Link>
            </div>
          ) : (
            <div className="p-6 text-center text-sm text-[#65676B] border-b border-[#E4E6EB]">
              <MapPin className="w-8 h-8 text-[#E4E6EB] mx-auto mb-2" />
              Select a charger on the map to view details
            </div>
          )}

          {/* Charger List */}
          <div className="flex-1 overflow-y-auto">
            <div className="px-4 py-2.5 bg-[#F7F8FA] border-b border-[#E4E6EB] sticky top-0">
              <span className="text-xs font-semibold text-[#050505]">
                {chargers.length.toLocaleString()} chargers
                {searchQuery && ` matching "${searchQuery}"`}
              </span>
            </div>
            <div className="divide-y divide-[#E4E6EB]">
              {chargers.map((charger) => (
                <button
                  key={charger.id}
                  onClick={() => {
                    setSelectedCharger(charger);
                    const map = mapInstanceRef.current;
                    if (map && charger.lat != null && charger.lng != null) {
                      map.setView([charger.lat, charger.lng], Math.max(map.getZoom(), 14), {
                        animate: true,
                      });
                    }
                  }}
                  className={`w-full text-left px-4 py-3 hover:bg-[#F7F8FA] transition-colors ${
                    selectedCharger?.id === charger.id
                      ? "bg-blue-50 border-l-2 border-l-[#1877F2]"
                      : ""
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{
                        backgroundColor: getNetworkColor(charger.network_name),
                      }}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-[#050505] truncate">
                        {charger.name}
                      </p>
                      <p className="text-xs text-[#65676B] truncate">
                        {[charger.network_name, charger.city, charger.state]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                    </div>
                    {charger.total_sessions > 0 && (
                      <span className="text-xs text-green-600 font-medium flex-shrink-0">
                        {charger.total_sessions} sessions
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="px-6 py-3 bg-red-50 border-t border-red-200 text-sm text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}
