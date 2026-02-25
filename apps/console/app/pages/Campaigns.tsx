import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Plus, Loader2 } from "lucide-react";
import { StatusPill } from "../components/StatusPill";
import { Progress } from "../components/ui/progress";
import { listCampaigns, type Campaign } from "../services/api";

function centsToDollars(cents: number): string {
  return (cents / 100).toLocaleString("en-US", { minimumFractionDigits: 0 });
}

export function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");

  useEffect(() => {
    loadCampaigns();
  }, [statusFilter]);

  async function loadCampaigns() {
    try {
      setLoading(true);
      const params: { status?: string; limit: number } = { limit: 50 };
      if (statusFilter) params.status = statusFilter;
      const { campaigns: data } = await listCampaigns(params);
      setCampaigns(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load campaigns");
    } finally {
      setLoading(false);
    }
  }

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

      {/* Status Filter */}
      <div className="flex gap-2 mb-4">
        {["", "active", "paused", "draft", "exhausted", "completed"].map(
          (s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 text-xs font-medium border transition-colors ${
                statusFilter === s
                  ? "bg-[#1877F2] text-white border-[#1877F2]"
                  : "bg-white text-[#65676B] border-[#E4E6EB] hover:bg-[#F7F8FA]"
              }`}
            >
              {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          )
        )}
      </div>

      {error && (
        <div className="p-4 mb-4 bg-red-50 border border-red-200 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-[#1877F2]" />
        </div>
      ) : (
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
                </tr>
              </thead>
              <tbody>
                {campaigns.length === 0 ? (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-6 py-8 text-center text-sm text-[#65676B]"
                    >
                      No campaigns found.{" "}
                      <Link
                        to="/campaigns/create"
                        className="text-[#1877F2] hover:underline"
                      >
                        Create your first campaign
                      </Link>
                    </td>
                  </tr>
                ) : (
                  campaigns.map((campaign) => {
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
                            className="text-sm text-[#050505] hover:text-[#1877F2] font-medium"
                          >
                            {campaign.name}
                          </Link>
                        </td>
                        <td className="px-6 py-4">
                          <StatusPill status={campaign.status} />
                        </td>
                        <td className="px-6 py-4 text-sm text-[#65676B]">
                          {campaign.start_date
                            ? new Date(campaign.start_date).toLocaleDateString(
                                "en-US",
                                {
                                  month: "short",
                                  day: "numeric",
                                  year: "numeric",
                                }
                              )
                            : "—"}{" "}
                          -{" "}
                          {campaign.end_date
                            ? new Date(campaign.end_date).toLocaleDateString(
                                "en-US",
                                {
                                  month: "short",
                                  day: "numeric",
                                  year: "numeric",
                                }
                              )
                            : "Ongoing"}
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
                          {costPerSession > 0
                            ? `$${costPerSession.toFixed(2)}`
                            : "—"}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
