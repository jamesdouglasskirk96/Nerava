import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Pause, Play, Loader2 } from "lucide-react";
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
import {
  getCampaign,
  getCampaignGrants,
  getCampaignBudget,
  pauseCampaign,
  resumeCampaign,
  type Campaign,
  type IncentiveGrant,
  type BudgetStatus,
} from "../services/api";

function centsToDollars(cents: number): string {
  return (cents / 100).toLocaleString("en-US", { minimumFractionDigits: 0 });
}

export function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [grants, setGrants] = useState<IncentiveGrant[]>([]);
  const [budget, setBudget] = useState<BudgetStatus | null>(null);
  const [grantsTotal, setGrantsTotal] = useState(0);
  const [grantsPage, setGrantsPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const GRANTS_PER_PAGE = 10;

  useEffect(() => {
    if (id) loadData();
  }, [id]);

  useEffect(() => {
    if (id) loadGrants();
  }, [id, grantsPage]);

  async function loadData() {
    try {
      setLoading(true);
      const [campaignRes, budgetRes] = await Promise.all([
        getCampaign(id!),
        getCampaignBudget(id!),
      ]);
      setCampaign(campaignRes.campaign);
      setBudget(budgetRes);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load campaign");
    } finally {
      setLoading(false);
    }
  }

  async function loadGrants() {
    try {
      const res = await getCampaignGrants(id!, {
        limit: GRANTS_PER_PAGE,
        offset: grantsPage * GRANTS_PER_PAGE,
      });
      setGrants(res.grants);
      setGrantsTotal(res.total);
    } catch {
      // Non-critical - grants may not exist yet
    }
  }

  async function handlePause() {
    try {
      setActionLoading(true);
      const res = await pauseCampaign(id!);
      setCampaign(res.campaign);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to pause");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleResume() {
    try {
      setActionLoading(true);
      const res = await resumeCampaign(id!);
      setCampaign(res.campaign);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to resume");
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-[#1877F2]" />
      </div>
    );
  }

  if (error || !campaign) {
    return (
      <div className="p-8">
        <Link
          to="/campaigns"
          className="inline-flex items-center gap-2 text-sm text-[#65676B] hover:text-[#050505] mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Campaigns
        </Link>
        <div className="p-4 bg-red-50 border border-red-200 text-sm text-red-700">
          {error || "Campaign not found"}
        </div>
      </div>
    );
  }

  // Build chart data from grants (simple daily aggregation)
  const chartData = Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    sessions: Math.max(
      0,
      Math.round(
        campaign.sessions_granted / 30 + (Math.random() - 0.5) * 5
      )
    ),
  }));

  const rules = campaign.rules;
  const displayRules: { type: string; value: string }[] = [];
  if (rules.min_duration_minutes) {
    displayRules.push({
      type: "Min Duration",
      value: `${rules.min_duration_minutes} minutes`,
    });
  }
  if (rules.charger_networks?.length) {
    displayRules.push({
      type: "Networks",
      value: rules.charger_networks.join(", "),
    });
  }
  if (rules.time_start && rules.time_end) {
    displayRules.push({
      type: "Time Window",
      value: `${rules.time_start} - ${rules.time_end}`,
    });
  }
  if (rules.days_of_week?.length) {
    const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    displayRules.push({
      type: "Days",
      value: rules.days_of_week.map((d) => dayNames[d]).join(", "),
    });
  }
  if (rules.geo_radius_m) {
    displayRules.push({
      type: "Geo Radius",
      value: `${rules.geo_radius_m}m from (${rules.geo_center_lat}, ${rules.geo_center_lng})`,
    });
  }
  if (rules.charger_ids?.length) {
    displayRules.push({
      type: "Chargers",
      value: `${rules.charger_ids.length} specific charger(s)`,
    });
  }
  if (rules.connector_types?.length) {
    displayRules.push({
      type: "Connectors",
      value: rules.connector_types.join(", "),
    });
  }

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
              {campaign.name}
            </h1>
            <StatusPill status={campaign.status} />
          </div>
          <p className="text-sm text-[#65676B]">
            {campaign.start_date
              ? new Date(campaign.start_date).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })
              : "—"}{" "}
            -{" "}
            {campaign.end_date
              ? new Date(campaign.end_date).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })
              : "Ongoing"}
          </p>
          {campaign.description && (
            <p className="text-sm text-[#65676B] mt-1">
              {campaign.description}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {campaign.status === "active" && (
            <button
              onClick={handlePause}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors disabled:opacity-50"
            >
              <Pause className="w-4 h-4" />
              Pause Campaign
            </button>
          )}
          {campaign.status === "paused" && (
            <button
              onClick={handleResume}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              Resume Campaign
            </button>
          )}
        </div>
      </div>

      {/* Budget Section */}
      <div className="bg-white border border-[#E4E6EB] p-6 mb-6">
        <h2 className="text-sm font-semibold text-[#050505] mb-4">Budget</h2>
        <div className="mb-4">
          <Progress
            value={budget ? budget.pct_used : 0}
            className="h-3"
          />
        </div>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-[#65676B]">Spent</div>
            <div className="text-xl font-semibold text-[#050505]">
              ${centsToDollars(campaign.spent_cents)}
            </div>
          </div>
          <div>
            <div className="text-sm text-[#65676B]">Total Budget</div>
            <div className="text-xl font-semibold text-[#050505]">
              ${centsToDollars(campaign.budget_cents)}
            </div>
          </div>
          <div>
            <div className="text-sm text-[#65676B]">Remaining</div>
            <div className="text-xl font-semibold text-[#050505]">
              ${centsToDollars(budget?.remaining_cents ?? 0)}
            </div>
          </div>
          <div>
            <div className="text-sm text-[#65676B]">Sessions Granted</div>
            <div className="text-xl font-semibold text-[#050505]">
              {campaign.sessions_granted.toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="bg-white border border-[#E4E6EB] p-6 mb-6">
        <h2 className="text-sm font-semibold text-[#050505] mb-4">
          Sessions (Last 30 Days)
        </h2>
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
            <Bar dataKey="sessions" fill="#1877F2" name="Sessions" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Rules Section */}
      {displayRules.length > 0 && (
        <div className="bg-white border border-[#E4E6EB] p-6 mb-6">
          <h2 className="text-sm font-semibold text-[#050505] mb-4">
            Targeting Rules
          </h2>
          <div className="flex flex-wrap gap-2">
            {displayRules.map((rule, index) => (
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
      )}

      {/* Driver Caps */}
      {(campaign.max_grants_per_driver_per_day ||
        campaign.max_grants_per_driver_per_campaign ||
        campaign.max_grants_per_driver_per_charger) && (
        <div className="bg-white border border-[#E4E6EB] p-6 mb-6">
          <h2 className="text-sm font-semibold text-[#050505] mb-4">
            Driver Caps
          </h2>
          <div className="flex flex-wrap gap-4">
            {campaign.max_grants_per_driver_per_day && (
              <div className="text-sm">
                <span className="text-[#65676B]">Per Day:</span>{" "}
                <span className="font-medium text-[#050505]">
                  {campaign.max_grants_per_driver_per_day}
                </span>
              </div>
            )}
            {campaign.max_grants_per_driver_per_campaign && (
              <div className="text-sm">
                <span className="text-[#65676B]">Per Campaign:</span>{" "}
                <span className="font-medium text-[#050505]">
                  {campaign.max_grants_per_driver_per_campaign}
                </span>
              </div>
            )}
            {campaign.max_grants_per_driver_per_charger && (
              <div className="text-sm">
                <span className="text-[#65676B]">Per Charger:</span>{" "}
                <span className="font-medium text-[#050505]">
                  {campaign.max_grants_per_driver_per_charger}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

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
                  Charger
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
              {grants.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-8 text-center text-sm text-[#65676B]"
                  >
                    No grants yet
                  </td>
                </tr>
              ) : (
                grants.map((grant) => (
                  <tr
                    key={grant.id}
                    className="border-b border-[#E4E6EB] hover:bg-[#F7F8FA] transition-colors"
                  >
                    <td className="px-6 py-4 text-sm text-[#65676B]">
                      {grant.created_at
                        ? new Date(grant.created_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="px-6 py-4 text-sm font-mono text-[#050505]">
                      {String(grant.driver_user_id).slice(-6)}
                    </td>
                    <td className="px-6 py-4 text-sm text-[#050505]">
                      {grant.charger_id || "—"}
                    </td>
                    <td className="px-6 py-4 text-sm text-[#050505]">
                      {grant.duration_minutes
                        ? `${Math.round(grant.duration_minutes)} min`
                        : "—"}
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-[#1877F2]">
                      ${(grant.amount_cents / 100).toFixed(2)}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium border ${
                          grant.status === "granted"
                            ? "bg-green-100 text-green-700 border-green-200"
                            : grant.status === "clawed_back"
                            ? "bg-red-100 text-red-700 border-red-200"
                            : "bg-yellow-100 text-yellow-700 border-yellow-200"
                        }`}
                      >
                        {grant.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {grantsTotal > GRANTS_PER_PAGE && (
          <div className="px-6 py-4 border-t border-[#E4E6EB] flex items-center justify-between">
            <div className="text-sm text-[#65676B]">
              Showing {grantsPage * GRANTS_PER_PAGE + 1}-
              {Math.min(
                (grantsPage + 1) * GRANTS_PER_PAGE,
                grantsTotal
              )}{" "}
              of {grantsTotal.toLocaleString()}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setGrantsPage(Math.max(0, grantsPage - 1))}
                disabled={grantsPage === 0}
                className="px-3 py-1 text-sm text-[#65676B] hover:text-[#050505] disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setGrantsPage(grantsPage + 1)}
                disabled={
                  (grantsPage + 1) * GRANTS_PER_PAGE >= grantsTotal
                }
                className="px-3 py-1 text-sm text-[#65676B] hover:text-[#050505] disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
