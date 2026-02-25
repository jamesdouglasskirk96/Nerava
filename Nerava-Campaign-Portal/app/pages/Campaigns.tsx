import { Link } from "react-router";
import { Plus } from "lucide-react";
import { StatusPill } from "../components/StatusPill";
import { Progress } from "../components/ui/progress";

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
    startDate: "2026-01-15",
    endDate: "2026-03-15",
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
    startDate: "2026-01-01",
    endDate: "2026-03-31",
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
    startDate: "2025-12-20",
    endDate: "2026-02-28",
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
    startDate: "2026-02-01",
    endDate: null,
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
    startDate: "2025-11-15",
    endDate: "2026-01-15",
  },
  {
    id: 6,
    name: "Highway 183 Corridor Boost",
    status: "Draft" as const,
    budgetUsed: 0,
    budgetTotal: 15000,
    sessions: 0,
    costPerSession: 0,
    lift: 0,
    startDate: "2026-03-01",
    endDate: "2026-04-30",
  },
  {
    id: 7,
    name: "Evening Rush Hour Incentive",
    status: "Active" as const,
    budgetUsed: 6200,
    budgetTotal: 18000,
    sessions: 1240,
    costPerSession: 5.0,
    lift: 31.2,
    startDate: "2026-01-20",
    endDate: null,
  },
  {
    id: 8,
    name: "Holiday Weekend Special",
    status: "Completed" as const,
    budgetUsed: 5000,
    budgetTotal: 5000,
    sessions: 1250,
    costPerSession: 4.0,
    lift: 45.8,
    startDate: "2025-12-23",
    endDate: "2026-01-02",
  },
];

export function Campaigns() {
  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-[#050505]">Campaigns</h1>
          <p className="text-sm text-[#65676B] mt-1">
            Manage your incentive campaigns
          </p>
        </div>
        <Link
          to="/campaigns/create"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Campaign
        </Link>
      </div>

      {/* Campaigns Table */}
      <div className="bg-white border border-[#E4E6EB]">
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
                  Date Range
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
                      className="text-sm text-[#050505] hover:text-[#1877F2] font-medium"
                    >
                      {campaign.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4">
                    <StatusPill status={campaign.status} />
                  </td>
                  <td className="px-6 py-4 text-sm text-[#65676B]">
                    {new Date(campaign.startDate).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}{" "}
                    -{" "}
                    {campaign.endDate
                      ? new Date(campaign.endDate).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })
                      : "Ongoing"}
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
                    {campaign.costPerSession > 0
                      ? `$${campaign.costPerSession.toFixed(2)}`
                      : "—"}
                  </td>
                  <td className="px-6 py-4">
                    {campaign.lift > 0 ? (
                      <span className="text-sm text-green-600 font-medium">
                        +{campaign.lift}%
                      </span>
                    ) : (
                      <span className="text-sm text-[#65676B]">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
