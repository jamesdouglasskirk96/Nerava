import { useState } from "react";
import { MapPin, Plus } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Link } from "react-router";

const chargers = [
  {
    id: 1,
    name: "Tesla Supercharger Canyon Ridge",
    network: "Tesla Supercharger",
    address: "12600 Hill Country Blvd, Austin, TX 78738",
    lat: 30.3672,
    lng: -97.9653,
    utilization: "high",
    sessionsPerDay: 42,
    avgDuration: "38 min",
    peakSplit: 65,
    offPeakSplit: 35,
  },
  {
    id: 2,
    name: "ChargePoint Downtown Station 4",
    network: "ChargePoint",
    address: "123 E 6th Street, Austin, TX 78701",
    lat: 30.2672,
    lng: -97.7431,
    utilization: "medium",
    sessionsPerDay: 28,
    avgDuration: "45 min",
    peakSplit: 72,
    offPeakSplit: 28,
  },
  {
    id: 3,
    name: "Electrify America Congress Ave",
    network: "Electrify America",
    address: "5678 Congress Ave, Austin, TX 78745",
    lat: 30.2172,
    lng: -97.7531,
    utilization: "low",
    sessionsPerDay: 15,
    avgDuration: "32 min",
    peakSplit: 48,
    offPeakSplit: 52,
  },
  {
    id: 4,
    name: "EVgo Fast Charge West Austin",
    network: "EVgo",
    address: "3456 N Lamar Blvd, Austin, TX 78705",
    lat: 30.3172,
    lng: -97.7631,
    utilization: "medium",
    sessionsPerDay: 31,
    avgDuration: "41 min",
    peakSplit: 58,
    offPeakSplit: 42,
  },
  {
    id: 5,
    name: "Tesla Supercharger South Lamar",
    network: "Tesla Supercharger",
    address: "2901 S Lamar Blvd, Austin, TX 78704",
    lat: 30.2472,
    lng: -97.7831,
    utilization: "high",
    sessionsPerDay: 48,
    avgDuration: "35 min",
    peakSplit: 68,
    offPeakSplit: 32,
  },
];

const chartData = Array.from({ length: 14 }, (_, i) => ({
  day: i + 1,
  sessions: 35 + Math.sin(i / 2) * 8 + Math.random() * 6,
}));

export function ChargerExplorer() {
  const [selectedCharger, setSelectedCharger] = useState(chargers[0]);

  const getUtilizationColor = (utilization: string) => {
    switch (utilization) {
      case "high":
        return "#22C55E";
      case "medium":
        return "#EAB308";
      case "low":
        return "#EF4444";
      default:
        return "#65676B";
    }
  };

  return (
    <div className="h-full flex">
      {/* Map Panel */}
      <div className="flex-1 relative bg-[#F7F8FA]">
        {/* Mock Map */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative w-full h-full">
            {/* Grid background to simulate map */}
            <div className="absolute inset-0 opacity-20">
              <div
                className="w-full h-full"
                style={{
                  backgroundImage: `
                    linear-gradient(#E4E6EB 1px, transparent 1px),
                    linear-gradient(90deg, #E4E6EB 1px, transparent 1px)
                  `,
                  backgroundSize: "50px 50px",
                }}
              />
            </div>

            {/* Charger Pins */}
            {chargers.map((charger, index) => (
              <button
                key={charger.id}
                onClick={() => setSelectedCharger(charger)}
                className="absolute transform -translate-x-1/2 -translate-y-full transition-all hover:scale-110"
                style={{
                  left: `${30 + index * 15}%`,
                  top: `${35 + (index % 3) * 15}%`,
                }}
              >
                <div className="relative">
                  <MapPin
                    className="w-8 h-8 drop-shadow-lg"
                    fill={getUtilizationColor(charger.utilization)}
                    stroke="white"
                    strokeWidth={1.5}
                  />
                  {selectedCharger?.id === charger.id && (
                    <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2">
                      <div className="w-2 h-2 bg-[#1877F2] rounded-full animate-pulse" />
                    </div>
                  )}
                </div>
              </button>
            ))}

            {/* Map Legend */}
            <div className="absolute bottom-6 left-6 bg-white border border-[#E4E6EB] p-4 shadow-lg">
              <div className="text-xs font-semibold text-[#050505] mb-2">
                Utilization
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <MapPin
                    className="w-4 h-4"
                    fill="#22C55E"
                    stroke="white"
                    strokeWidth={1.5}
                  />
                  <span className="text-xs text-[#65676B]">High (35+ sessions/day)</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin
                    className="w-4 h-4"
                    fill="#EAB308"
                    stroke="white"
                    strokeWidth={1.5}
                  />
                  <span className="text-xs text-[#65676B]">Medium (20-34 sessions/day)</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin
                    className="w-4 h-4"
                    fill="#EF4444"
                    stroke="white"
                    strokeWidth={1.5}
                  />
                  <span className="text-xs text-[#65676B]">Low (&lt;20 sessions/day)</span>
                </div>
              </div>
            </div>

            {/* Map Controls */}
            <div className="absolute top-6 right-6 flex flex-col gap-2">
              <button className="w-10 h-10 bg-white border border-[#E4E6EB] flex items-center justify-center text-[#050505] font-semibold hover:bg-[#F7F8FA] transition-colors shadow-sm">
                +
              </button>
              <button className="w-10 h-10 bg-white border border-[#E4E6EB] flex items-center justify-center text-[#050505] font-semibold hover:bg-[#F7F8FA] transition-colors shadow-sm">
                −
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Detail Panel */}
      <div className="w-96 bg-white border-l border-[#E4E6EB] overflow-y-auto">
        <div className="p-6">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-[#050505] mb-1">
              {selectedCharger.name}
            </h2>
            <p className="text-sm text-[#65676B] mb-1">
              {selectedCharger.network}
            </p>
            <p className="text-sm text-[#65676B]">{selectedCharger.address}</p>
          </div>

          {/* Utilization Stats */}
          <div className="mb-6 p-4 bg-[#F7F8FA] border border-[#E4E6EB]">
            <h3 className="text-xs font-semibold text-[#050505] mb-3">
              Utilization
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-[#65676B] mb-1">
                  Sessions/Day
                </div>
                <div className="text-xl font-semibold text-[#050505]">
                  {selectedCharger.sessionsPerDay}
                </div>
              </div>
              <div>
                <div className="text-xs text-[#65676B] mb-1">Avg Duration</div>
                <div className="text-xl font-semibold text-[#050505]">
                  {selectedCharger.avgDuration}
                </div>
              </div>
            </div>
          </div>

          {/* Peak vs Off-Peak */}
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-[#050505] mb-2">
              Peak vs Off-Peak
            </h3>
            <div className="flex h-6 mb-2">
              <div
                className="bg-[#1877F2] flex items-center justify-center"
                style={{ width: `${selectedCharger.peakSplit}%` }}
              >
                {selectedCharger.peakSplit > 20 && (
                  <span className="text-xs text-white font-medium">
                    {selectedCharger.peakSplit}%
                  </span>
                )}
              </div>
              <div
                className="bg-[#E4E6EB] flex items-center justify-center"
                style={{ width: `${selectedCharger.offPeakSplit}%` }}
              >
                {selectedCharger.offPeakSplit > 20 && (
                  <span className="text-xs text-[#65676B] font-medium">
                    {selectedCharger.offPeakSplit}%
                  </span>
                )}
              </div>
            </div>
            <div className="flex justify-between text-xs text-[#65676B]">
              <span>Peak (6am-10pm)</span>
              <span>Off-Peak (10pm-6am)</span>
            </div>
          </div>

          {/* Chart */}
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-[#050505] mb-3">
              Sessions (Last 14 Days)
            </h3>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E4E6EB" />
                <XAxis
                  dataKey="day"
                  stroke="#65676B"
                  style={{ fontSize: "10px" }}
                />
                <YAxis stroke="#65676B" style={{ fontSize: "10px" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #E4E6EB",
                    borderRadius: "4px",
                    fontSize: "12px",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="sessions"
                  stroke="#1877F2"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Action Button */}
          <Link
            to="/campaigns/create"
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Campaign for This Charger
          </Link>
        </div>
      </div>
    </div>
  );
}
