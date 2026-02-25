import { useParams, Link } from "react-router";
import { ArrowLeft, Pause, Edit } from "lucide-react";
import { StatusPill } from "../components/StatusPill";
import { Progress } from "../components/ui/progress";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const campaignData = {
  id: 1,
  name: "Austin Off-Peak Boost",
  status: "Active" as const,
  startDate: "2026-01-15",
  endDate: "2026-03-15",
  budgetUsed: 14500,
  budgetTotal: 25000,
  baselineSessions: 180,
  incentivizedSessions: 256,
  lift: 42.2,
  projectedExhaustion: "2026-02-28",
};

const chartData = Array.from({ length: 30 }, (_, i) => ({
  day: i + 1,
  baseline: 150 + Math.random() * 40,
  incentivized: 80 + Math.random() * 30,
}));

const rules = [
  { type: "Time of Day", value: "10:00 PM - 6:00 AM" },
  { type: "Geographic Zone", value: "Downtown Austin (2 mi radius)" },
  { type: "Charging Network", value: "Tesla Supercharger, ChargePoint" },
  { type: "Minimum Duration", value: "30 minutes" },
];

const grants = [
  {
    id: 1,
    timestamp: "2026-02-23 14:32:15",
    driverId: "A4F8C2",
    chargerName: "Tesla Supercharger Canyon Ridge",
    duration: "45 min",
    amount: 2.0,
    status: "Completed",
  },
  {
    id: 2,
    timestamp: "2026-02-23 14:18:42",
    driverId: "B7K2M1",
    chargerName: "ChargePoint Downtown Station 4",
    duration: "38 min",
    amount: 2.0,
    status: "Completed",
  },
  {
    id: 3,
    timestamp: "2026-02-23 13:55:23",
    driverId: "C3M9N5",
    chargerName: "Tesla Supercharger South Lamar",
    duration: "52 min",
    amount: 2.0,
    status: "Completed",
  },
  {
    id: 4,
    timestamp: "2026-02-23 13:41:07",
    driverId: "D1N5P8",
    chargerName: "ChargePoint Tech Ridge Plaza",
    duration: "41 min",
    amount: 2.0,
    status: "Completed",
  },
  {
    id: 5,
    timestamp: "2026-02-23 13:22:59",
    driverId: "E9P1Q4",
    chargerName: "Tesla Supercharger Canyon Ridge",
    duration: "47 min",
    amount: 2.0,
    status: "Completed",
  },
  {
    id: 6,
    timestamp: "2026-02-23 12:58:31",
    driverId: "F2Q4R7",
    chargerName: "Electrify America Congress Ave",
    duration: "33 min",
    amount: 2.0,
    status: "Completed",
  },
  {
    id: 7,
    timestamp: "2026-02-23 12:35:18",
    driverId: "G5R7S1",
    chargerName: "ChargePoint Barton Creek",
    duration: "56 min",
    amount: 2.0,
    status: "Completed",
  },
  {
    id: 8,
    timestamp: "2026-02-23 12:14:45",
    driverId: "H8S1T3",
    chargerName: "Tesla Supercharger South Lamar",
    duration: "39 min",
    amount: 2.0,
    status: "Completed",
  },
  {
    id: 9,
    timestamp: "2026-02-23 11:52:33",
    driverId: "I1T3U6",
    chargerName: "ChargePoint Downtown Station 4",
    duration: "44 min",
    amount: 2.0,
    status: "Pending",
  },
  {
    id: 10,
    timestamp: "2026-02-23 11:28:19",
    driverId: "J4U6V9",
    chargerName: "Tesla Supercharger Canyon Ridge",
    duration: "50 min",
    amount: 2.0,
    status: "Completed",
  },
];

export function CampaignDetail() {
  const { id } = useParams();

  return (
    <div className="p-8">
      {/* Back Button */}
      <Link
        to="/campaigns"
        className="inline-flex items-center gap-2 text-sm text-[#65676B] hover:text-[#050505] mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Campaigns
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-semibold text-[#050505]">
              {campaignData.name}
            </h1>
            <StatusPill status={campaignData.status} />
          </div>
          <p className="text-sm text-[#65676B]">
            {new Date(campaignData.startDate).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
            })}{" "}
            -{" "}
            {new Date(campaignData.endDate).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
            })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="inline-flex items-center gap-2 px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors">
            <Pause className="w-4 h-4" />
            Pause Campaign
          </button>
          <button className="inline-flex items-center gap-2 px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors">
            <Edit className="w-4 h-4" />
            Edit
          </button>
        </div>
      </div>

      {/* Budget Section */}
      <div className="bg-white border border-[#E4E6EB] p-6 mb-6">
        <h2 className="text-sm font-semibold text-[#050505] mb-4">Budget</h2>
        <div className="mb-4">
          <Progress
            value={(campaignData.budgetUsed / campaignData.budgetTotal) * 100}
            className="h-3"
          />
        </div>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-[#65676B]">Spent</div>
            <div className="text-xl font-semibold text-[#050505]">
              ${campaignData.budgetUsed.toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-sm text-[#65676B]">Total Budget</div>
            <div className="text-xl font-semibold text-[#050505]">
              ${campaignData.budgetTotal.toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-sm text-[#65676B]">Remaining</div>
            <div className="text-xl font-semibold text-[#050505]">
              $
              {(
                campaignData.budgetTotal - campaignData.budgetUsed
              ).toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-sm text-[#65676B]">
              Projected Exhaustion
            </div>
            <div className="text-sm text-[#050505]">
              {new Date(campaignData.projectedExhaustion).toLocaleDateString(
                "en-US",
                {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                }
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Performance Section */}
      <div className="bg-white border border-[#E4E6EB] p-6 mb-6">
        <h2 className="text-sm font-semibold text-[#050505] mb-4">
          Performance
        </h2>
        <div className="grid grid-cols-3 gap-6 mb-6">
          <div>
            <div className="text-xs text-[#65676B] mb-1">
              Baseline (sessions/day)
            </div>
            <div className="text-3xl font-semibold text-[#050505]">
              {campaignData.baselineSessions}
            </div>
          </div>
          <div>
            <div className="text-xs text-[#65676B] mb-1">
              With Incentive (sessions/day)
            </div>
            <div className="text-3xl font-semibold text-[#050505]">
              {campaignData.incentivizedSessions}
            </div>
          </div>
          <div>
            <div className="text-xs text-[#65676B] mb-1">Lift</div>
            <div className="text-3xl font-semibold text-green-600">
              +{campaignData.lift}%
            </div>
          </div>
        </div>

        {/* Chart */}
        <div>
          <h3 className="text-xs font-medium text-[#65676B] mb-3">
            Daily Sessions (Last 30 Days)
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E4E6EB" />
              <XAxis
                dataKey="day"
                stroke="#65676B"
                style={{ fontSize: "12px" }}
              />
              <YAxis stroke="#65676B" style={{ fontSize: "12px" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "white",
                  border: "1px solid #E4E6EB",
                  borderRadius: "4px",
                  fontSize: "12px",
                }}
              />
              <Bar
                dataKey="baseline"
                stackId="a"
                fill="#E4E6EB"
                name="Baseline"
              />
              <Bar
                dataKey="incentivized"
                stackId="a"
                fill="#1877F2"
                name="Incentivized"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Rules Section */}
      <div className="bg-white border border-[#E4E6EB] p-6 mb-6">
        <h2 className="text-sm font-semibold text-[#050505] mb-4">
          Targeting Rules
        </h2>
        <div className="flex flex-wrap gap-2">
          {rules.map((rule, index) => (
            <div
              key={index}
              className="inline-flex items-center px-3 py-1.5 bg-[#F7F8FA] border border-[#E4E6EB] text-sm"
            >
              <span className="text-[#65676B]">{rule.type}:</span>
              <span className="ml-1.5 text-[#050505] font-medium">
                {rule.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Grants Table */}
      <div className="bg-white border border-[#E4E6EB]">
        <div className="px-6 py-4 border-b border-[#E4E6EB]">
          <h2 className="text-sm font-semibold text-[#050505]">
            Recent Grants
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#F7F8FA] border-b border-[#E4E6EB]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Driver ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Charger Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Amount Granted
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {grants.map((grant) => (
                <tr
                  key={grant.id}
                  className="border-b border-[#E4E6EB] hover:bg-[#F7F8FA] transition-colors"
                >
                  <td className="px-6 py-4 text-sm text-[#65676B]">
                    {grant.timestamp}
                  </td>
                  <td className="px-6 py-4 text-sm font-mono text-[#050505]">
                    {grant.driverId}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#050505]">
                    {grant.chargerName}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#050505]">
                    {grant.duration}
                  </td>
                  <td className="px-6 py-4 text-sm font-semibold text-[#1877F2]">
                    ${grant.amount.toFixed(2)}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium border ${
                        grant.status === "Completed"
                          ? "bg-green-100 text-green-700 border-green-200"
                          : "bg-yellow-100 text-yellow-700 border-yellow-200"
                      }`}
                    >
                      {grant.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 border-t border-[#E4E6EB] flex items-center justify-between">
          <div className="text-sm text-[#65676B]">Showing 1-10 of 2,890</div>
          <div className="flex items-center gap-2">
            <button className="px-3 py-1 text-sm text-[#65676B] hover:text-[#050505] disabled:opacity-50">
              Previous
            </button>
            <button className="px-3 py-1 text-sm text-[#65676B] hover:text-[#050505]">
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
