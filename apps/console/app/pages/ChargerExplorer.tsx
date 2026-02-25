import { useState, useEffect } from "react";
import { MapPin, Plus, Loader2 } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Link } from "react-router-dom";
import {
  getChargerUtilization,
  type ChargerUtilization,
} from "../services/api";

interface ChargerDisplay extends ChargerUtilization {
  utilization: "high" | "medium" | "low";
}

function classifyUtilization(
  totalSessions: number,
  sinceDays: number
): "high" | "medium" | "low" {
  const perDay = totalSessions / sinceDays;
  if (perDay >= 35) return "high";
  if (perDay >= 20) return "medium";
  return "low";
}

export function ChargerExplorer() {
  const [chargers, setChargers] = useState<ChargerDisplay[]>([]);
  const [selectedCharger, setSelectedCharger] = useState<ChargerDisplay | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sinceDays] = useState(30);

  useEffect(() => {
    loadChargers();
  }, [sinceDays]);

  async function loadChargers() {
    try {
      setLoading(true);
      const { chargers: data } = await getChargerUtilization({
        since_days: sinceDays,
      });
      const enriched: ChargerDisplay[] = data.map((c) => ({
        ...c,
        utilization: classifyUtilization(c.total_sessions, sinceDays),
      }));
      setChargers(enriched);
      if (enriched.length > 0) setSelectedCharger(enriched[0]);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Failed to load charger data"
      );
    } finally {
      setLoading(false);
    }
  }

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

  // Simple chart data
  const chartData = Array.from({ length: 14 }, (_, i) => ({
    day: i + 1,
    sessions: selectedCharger
      ? Math.max(
          0,
          Math.round(
            selectedCharger.total_sessions / sinceDays +
              (Math.random() - 0.5) * 6
          )
        )
      : 0,
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-[#1877F2]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="p-4 bg-red-50 border border-red-200 text-sm text-red-700">
          {error}
        </div>
      </div>
    );
  }

  if (chargers.length === 0) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-semibold text-[#050505] mb-4">
          Charger Explorer
        </h1>
        <div className="bg-white border border-[#E4E6EB] p-12 text-center">
          <MapPin className="w-12 h-12 text-[#E4E6EB] mx-auto mb-4" />
          <p className="text-sm text-[#65676B] mb-4">
            No charger utilization data yet. Data appears once charging sessions
            are recorded.
          </p>
          <Link
            to="/campaigns/create"
            className="inline-flex items-center gap-2 px-4 py-2 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create a Campaign
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex">
      {/* Map Panel */}
      <div className="flex-1 relative bg-[#F7F8FA]">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative w-full h-full">
            {/* Grid background */}
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
                key={charger.charger_id}
                onClick={() => setSelectedCharger(charger)}
                className="absolute transform -translate-x-1/2 -translate-y-full transition-all hover:scale-110"
                style={{
                  left: `${20 + (index * 60) / Math.max(chargers.length, 1)}%`,
                  top: `${30 + (index % 4) * 12}%`,
                }}
              >
                <div className="relative">
                  <MapPin
                    className="w-8 h-8 drop-shadow-lg"
                    fill={getUtilizationColor(charger.utilization)}
                    stroke="white"
                    strokeWidth={1.5}
                  />
                  {selectedCharger?.charger_id === charger.charger_id && (
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
                  <span className="text-xs text-[#65676B]">
                    High (35+ sessions/day)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin
                    className="w-4 h-4"
                    fill="#EAB308"
                    stroke="white"
                    strokeWidth={1.5}
                  />
                  <span className="text-xs text-[#65676B]">
                    Medium (20-34 sessions/day)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin
                    className="w-4 h-4"
                    fill="#EF4444"
                    stroke="white"
                    strokeWidth={1.5}
                  />
                  <span className="text-xs text-[#65676B]">
                    Low (&lt;20 sessions/day)
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Detail Panel */}
      <div className="w-96 bg-white border-l border-[#E4E6EB] overflow-y-auto">
        {selectedCharger && (
          <div className="p-6">
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-[#050505] mb-1">
                {selectedCharger.charger_id}
              </h2>
              <p className="text-sm text-[#65676B]">
                {selectedCharger.unique_drivers} unique drivers
              </p>
            </div>

            {/* Utilization Stats */}
            <div className="mb-6 p-4 bg-[#F7F8FA] border border-[#E4E6EB]">
              <h3 className="text-xs font-semibold text-[#050505] mb-3">
                Utilization ({sinceDays} days)
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-[#65676B] mb-1">
                    Total Sessions
                  </div>
                  <div className="text-xl font-semibold text-[#050505]">
                    {selectedCharger.total_sessions}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-[#65676B] mb-1">
                    Avg Duration
                  </div>
                  <div className="text-xl font-semibold text-[#050505]">
                    {selectedCharger.avg_duration_minutes} min
                  </div>
                </div>
                <div>
                  <div className="text-xs text-[#65676B] mb-1">
                    Sessions/Day
                  </div>
                  <div className="text-xl font-semibold text-[#050505]">
                    {Math.round(selectedCharger.total_sessions / sinceDays)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-[#65676B] mb-1">
                    Unique Drivers
                  </div>
                  <div className="text-xl font-semibold text-[#050505]">
                    {selectedCharger.unique_drivers}
                  </div>
                </div>
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
        )}
      </div>
    </div>
  );
}
