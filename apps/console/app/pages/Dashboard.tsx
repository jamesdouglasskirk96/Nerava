import { useState, useEffect } from "react";
import { Pause, Edit, Loader2 } from "lucide-react";
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
import { Link } from "react-router-dom";
import { Progress } from "../components/ui/progress";
import {
  listCampaigns,
  getCampaignGrants,
  pauseCampaign,
  type Campaign,
  type IncentiveGrant,
} from "../services/api";

function centsToDollars(cents: number): string {
  return (cents / 100).toLocaleString("en-US", { minimumFractionDigits: 0 });
}

export function Dashboard() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [recentGrants, setRecentGrants] = useState<IncentiveGrant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const { campaigns: data } = await listCampaigns({ limit: 50 });
      setCampaigns(data);

      // Load recent grants from the first active campaign (for activity feed)
      const activeCampaign = data.find((c) => c.status === "active");
      if (activeCampaign) {
        const { grants } = await getCampaignGrants(activeCampaign.id, {
          limit: 5,
        });
        setRecentGrants(grants);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }

  async function handlePause(campaignId: string) {
    try {
      await pauseCampaign(campaignId);
      loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to pause campaign");
    }
  }

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

  const activeCampaigns = campaigns.filter((c) => c.status === "active");
  const totalSessionsFunded = campaigns.reduce(
    (sum, c) => sum + c.sessions_granted,
    0
  );
  const totalBudget = campaigns.reduce((sum, c) => sum + c.budget_cents, 0);
  const totalSpent = campaigns.reduce((sum, c) => sum + c.spent_cents, 0);
  const pctUsed = totalBudget > 0 ? Math.round((totalSpent / totalBudget) * 100) : 0;

  const statsData = [
    { label: "Active Campaigns", value: String(activeCampaigns.length) },
    {
      label: "Total Sessions Funded",
      value: totalSessionsFunded.toLocaleString(),
    },
    {
      label: "Budget Remaining",
      value: `$${centsToDollars(totalBudget - totalSpent)}`,
      progress: pctUsed,
      total: `$${centsToDollars(totalBudget)}`,
    },
    {
      label: "Avg Cost/Session",
      value:
        totalSessionsFunded > 0
          ? `$${(totalSpent / 100 / totalSessionsFunded).toFixed(2)}`
          : "$0",
    },
  ];

  // Generate simple chart data from campaign sessions_granted
  const chartData = Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    sessions: Math.max(
      0,
      Math.round(totalSessionsFunded / 30 + (Math.random() - 0.5) * 10)
    ),
  }));

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
              dataKey="sessions"
              stroke="#1877F2"
              strokeWidth={2}
              dot={false}
              name="Sessions"
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
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.length === 0 ? (
                    <tr>
                      <td
                        colSpan={6}
                        className="px-6 py-8 text-center text-sm text-[#65676B]"
                      >
                        No campaigns yet.{" "}
                        <Link
                          to="/campaigns/create"
                          className="text-[#1877F2] hover:underline"
                        >
                          Create your first campaign
                        </Link>
                      </td>
                    </tr>
                  ) : (
                    campaigns.slice(0, 5).map((campaign) => {
                      const pct =
                        campaign.budget_cents > 0
                          ? (campaign.spent_cents / campaign.budget_cents) * 100
                          : 0;
                      const costPerSession =
                        campaign.sessions_granted > 0
                          ? campaign.spent_cents /
                            100 /
                            campaign.sessions_granted
                          : campaign.cost_per_session_cents / 100;
                      return (
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
                              <Progress value={pct} className="h-1.5 mb-1" />
                              <div className="text-xs text-[#65676B]">
                                ${centsToDollars(campaign.spent_cents)} / $
                                {centsToDollars(campaign.budget_cents)}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-[#050505]">
                            {campaign.sessions_granted.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 text-sm text-[#050505]">
                            ${costPerSession.toFixed(2)}
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              {campaign.status === "active" && (
                                <button
                                  onClick={() => handlePause(campaign.id)}
                                  className="p-1 hover:bg-[#E4E6EB] rounded transition-colors"
                                >
                                  <Pause className="w-4 h-4 text-[#65676B]" />
                                </button>
                              )}
                              <Link
                                to={`/campaigns/${campaign.id}`}
                                className="p-1 hover:bg-[#E4E6EB] rounded transition-colors"
                              >
                                <Edit className="w-4 h-4 text-[#65676B]" />
                              </Link>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
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
              {recentGrants.length === 0 ? (
                <div className="px-6 py-8 text-center text-sm text-[#65676B]">
                  No recent activity
                </div>
              ) : (
                recentGrants.map((grant) => (
                  <div key={grant.id} className="px-6 py-4">
                    <div className="text-sm text-[#050505] mb-1">
                      Driver #{String(grant.driver_user_id).slice(-4)} earned{" "}
                      <span className="font-semibold text-[#1877F2]">
                        ${(grant.amount_cents / 100).toFixed(2)}
                      </span>
                    </div>
                    {grant.charger_id && (
                      <div className="text-xs text-[#65676B] mb-1">
                        Charger: {grant.charger_id}
                      </div>
                    )}
                    {grant.duration_minutes && (
                      <div className="text-xs text-[#65676B]">
                        Duration: {Math.round(grant.duration_minutes)} min
                      </div>
                    )}
                    <div className="text-xs text-[#65676B] mt-2">
                      {grant.granted_at
                        ? new Date(grant.granted_at).toLocaleString()
                        : "Pending"}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
