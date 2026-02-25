import { TrendingUp, TrendingDown, Pause, Edit } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { StatusPill } from "../components/StatusPill";
import { Link } from "react-router";
import { Progress } from "../components/ui/progress";

const statsData = [
  { label: "Active Campaigns", value: "8", trend: null },
  { label: "Total Sessions Funded", value: "12,482", trend: null },
  {
    label: "Budget Remaining",
    value: "$127,450",
    progress: 45,
    total: "$230,000",
  },
  { label: "Avg Lift %", value: "+34.2%", trend: "up" },
];

const chartData = Array.from({ length: 30 }, (_, i) => ({
  day: i + 1,
  baseline: 180 + Math.sin(i / 3) * 20 + Math.random() * 15,
  incentivized: 240 + Math.sin(i / 3) * 30 + Math.random() * 20,
}));

const campaigns = [
  {
    id: 1,
    name: "Austin Off-Peak Boost",
    status: "Active" as const,
    budgetUsed: 14500,
    budgetTotal: 25000,
    sessions: 2890,
    costPerSession: 5.02,
    lift: 42.3,
  },
  {
    id: 2,
    name: "Tesla Supercharger Network Q1",
    status: "Active" as const,
    budgetUsed: 8200,
    budgetTotal: 50000,
    sessions: 4100,
    costPerSession: 2.0,
    lift: 28.7,
  },
  {
    id: 3,
    name: "Weekend Corridor Campaign",
    status: "Paused" as const,
    budgetUsed: 12000,
    budgetTotal: 15000,
    sessions: 1820,
    costPerSession: 6.59,
    lift: 51.2,
  },
  {
    id: 4,
    name: "New Driver Acquisition - West",
    status: "Active" as const,
    budgetUsed: 4800,
    budgetTotal: 20000,
    sessions: 960,
    costPerSession: 5.0,
    lift: 18.9,
  },
  {
    id: 5,
    name: "Downtown Utilization Push",
    status: "Exhausted" as const,
    budgetUsed: 10000,
    budgetTotal: 10000,
    sessions: 2500,
    costPerSession: 4.0,
    lift: 38.4,
  },
];

const recentActivity = [
  {
    id: 1,
    driver: "Driver #A4F8",
    amount: 2.0,
    charger: "Tesla Supercharger Canyon Ridge",
    campaign: "Austin Off-Peak Boost",
    time: "2 minutes ago",
  },
  {
    id: 2,
    driver: "Driver #B7K2",
    amount: 5.0,
    charger: "ChargePoint Downtown Station 4",
    campaign: "Downtown Utilization Push",
    time: "8 minutes ago",
  },
  {
    id: 3,
    driver: "Driver #C3M9",
    amount: 2.0,
    charger: "Electrify America Highway 183",
    campaign: "Weekend Corridor Campaign",
    time: "12 minutes ago",
  },
  {
    id: 4,
    driver: "Driver #D1N5",
    amount: 3.5,
    charger: "EVgo Fast Charge West Austin",
    campaign: "New Driver Acquisition - West",
    time: "18 minutes ago",
  },
  {
    id: 5,
    driver: "Driver #E9P1",
    amount: 2.0,
    charger: "Tesla Supercharger Canyon Ridge",
    campaign: "Austin Off-Peak Boost",
    time: "23 minutes ago",
  },
];

export function Dashboard() {
  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[#050505]">Dashboard</h1>
        <p className="text-sm text-[#65676B] mt-1">
          Overview of your campaign performance
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {statsData.map((stat, index) => (
          <div
            key={index}
            className="bg-white border border-[#E4E6EB] p-5 hover:shadow-sm transition-shadow"
          >
            <div className="text-xs text-[#65676B] mb-1">{stat.label}</div>
            <div className="flex items-baseline gap-2">
              <div className="text-2xl font-semibold text-[#050505]">
                {stat.value}
              </div>
              {stat.trend && (
                <div
                  className={`flex items-center gap-1 text-xs ${
                    stat.trend === "up" ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {stat.trend === "up" ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                </div>
              )}
            </div>
            {stat.progress !== undefined && (
              <div className="mt-3">
                <Progress value={stat.progress} className="h-1.5" />
                <div className="text-xs text-[#65676B] mt-1.5">
                  {stat.progress}% of {stat.total}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="bg-white border border-[#E4E6EB] p-6 mb-8">
        <div className="mb-4">
          <h2 className="text-sm font-semibold text-[#050505]">
            Sessions per Day
          </h2>
          <p className="text-xs text-[#65676B] mt-1">Last 30 days</p>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
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
            <Line
              type="monotone"
              dataKey="baseline"
              stroke="#65676B"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="Baseline"
            />
            <Line
              type="monotone"
              dataKey="incentivized"
              stroke="#1877F2"
              strokeWidth={2}
              dot={false}
              name="With Incentive"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-3 gap-8">
        {/* Active Campaigns Table */}
        <div className="col-span-2">
          <div className="bg-white border border-[#E4E6EB]">
            <div className="px-6 py-4 border-b border-[#E4E6EB] flex items-center justify-between">
              <h2 className="text-sm font-semibold text-[#050505]">
                Active Campaigns
              </h2>
              <Link
                to="/campaigns/create"
                className="text-xs text-[#1877F2] hover:underline"
              >
                Create New
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#F7F8FA] border-b border-[#E4E6EB]">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                      Campaign Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                      Budget Used
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                      Sessions
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                      Cost/Session
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                      Lift %
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.map((campaign) => (
                    <tr
                      key={campaign.id}
                      className="border-b border-[#E4E6EB] hover:bg-[#F7F8FA] transition-colors"
                    >
                      <td className="px-6 py-4">
                        <Link
                          to={`/campaigns/${campaign.id}`}
                          className="text-sm text-[#050505] hover:text-[#1877F2]"
                        >
                          {campaign.name}
                        </Link>
                      </td>
                      <td className="px-6 py-4">
                        <StatusPill status={campaign.status} />
                      </td>
                      <td className="px-6 py-4">
                        <div className="w-32">
                          <Progress
                            value={
                              (campaign.budgetUsed / campaign.budgetTotal) * 100
                            }
                            className="h-1.5 mb-1"
                          />
                          <div className="text-xs text-[#65676B]">
                            ${campaign.budgetUsed.toLocaleString()} / $
                            {campaign.budgetTotal.toLocaleString()}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-[#050505]">
                        {campaign.sessions.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-sm text-[#050505]">
                        ${campaign.costPerSession.toFixed(2)}
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-green-600 font-medium">
                          +{campaign.lift}%
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button className="p-1 hover:bg-[#E4E6EB] rounded transition-colors">
                            <Pause className="w-4 h-4 text-[#65676B]" />
                          </button>
                          <button className="p-1 hover:bg-[#E4E6EB] rounded transition-colors">
                            <Edit className="w-4 h-4 text-[#65676B]" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="col-span-1">
          <div className="bg-white border border-[#E4E6EB]">
            <div className="px-6 py-4 border-b border-[#E4E6EB]">
              <h2 className="text-sm font-semibold text-[#050505]">
                Recent Activity
              </h2>
            </div>
            <div className="divide-y divide-[#E4E6EB]">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="px-6 py-4">
                  <div className="text-sm text-[#050505] mb-1">
                    {activity.driver} earned{" "}
                    <span className="font-semibold text-[#1877F2]">
                      ${activity.amount.toFixed(2)}
                    </span>
                  </div>
                  <div className="text-xs text-[#65676B] mb-1">
                    {activity.charger}
                  </div>
                  <div className="text-xs text-[#65676B]">
                    Campaign: {activity.campaign}
                  </div>
                  <div className="text-xs text-[#65676B] mt-2">
                    {activity.time}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
