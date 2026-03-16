import { useState, useEffect } from "react";
import { CreditCard, Download, Loader2 } from "lucide-react";
import { listCampaigns, type Campaign } from "../services/api";

export function Billing() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const { campaigns: data } = await listCampaigns({ limit: 100 });
      setCampaigns(data);
    } catch {
      // Silently fail - empty state will show
    } finally {
      setLoading(false);
    }
  }

  const totalBudget = campaigns.reduce((sum, c) => sum + c.budget_cents, 0);
  const totalSpent = campaigns.reduce((sum, c) => sum + c.spent_cents, 0);
  const totalRemaining = totalBudget - totalSpent;

  // Build transaction list from campaign data
  const transactions = campaigns
    .map((c) => ({
      id: c.id,
      date: c.created_at,
      description: `Campaign: ${c.name}`,
      amount: -c.budget_cents,
      spent: c.spent_cents,
      status: c.status === "active" ? "Active" : c.status === "draft" ? "Draft" : c.status === "exhausted" ? "Exhausted" : "Completed",
    }))
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-[#1877F2]" />
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[#050505]">Billing</h1>
        <p className="text-sm text-[#65676B] mt-1">
          Campaign budget overview and spending history
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-8">
        {/* Total Budget Card */}
        <div className="bg-white border border-[#E4E6EB] p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="text-xs text-[#65676B] mb-1">
                Total Budget Allocated
              </div>
              <div className="text-3xl font-semibold text-[#050505]">
                ${(totalBudget / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
            </div>
            <div className="w-12 h-12 bg-[#F7F8FA] rounded-full flex items-center justify-center">
              <CreditCard className="w-6 h-6 text-[#1877F2]" />
            </div>
          </div>
        </div>

        {/* Spent Card */}
        <div className="bg-white border border-[#E4E6EB] p-6">
          <div>
            <div className="text-xs text-[#65676B] mb-1">
              Total Spent
            </div>
            <div className="text-3xl font-semibold text-[#050505]">
              ${(totalSpent / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-[#65676B] mt-2">
              Across {campaigns.filter((c) => c.sessions_granted > 0).length} campaigns
            </div>
          </div>
        </div>

        {/* Remaining Card */}
        <div className="bg-white border border-[#E4E6EB] p-6">
          <div>
            <div className="text-xs text-[#65676B] mb-1">
              Remaining Budget
            </div>
            <div className={`text-3xl font-semibold ${totalRemaining > 0 ? "text-green-600" : "text-[#050505]"}`}>
              ${(totalRemaining / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-[#65676B] mt-2">
              {campaigns.filter((c) => c.status === "active").length} active campaign{campaigns.filter((c) => c.status === "active").length !== 1 ? "s" : ""}
            </div>
          </div>
        </div>
      </div>

      {/* Campaign Spending Table */}
      <div className="bg-white border border-[#E4E6EB]">
        <div className="px-6 py-4 border-b border-[#E4E6EB] flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[#050505]">
            Campaign Spending
          </h2>
          <button className="inline-flex items-center gap-2 px-4 py-2 border border-[#E4E6EB] text-sm text-[#050505] hover:bg-[#F7F8FA] transition-colors">
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
        {transactions.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <CreditCard className="w-10 h-10 text-[#E4E6EB] mx-auto mb-3" />
            <p className="text-sm text-[#65676B] mb-1">No campaigns yet</p>
            <p className="text-xs text-[#65676B]">
              Create a campaign to start tracking spending.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[#F7F8FA] border-b border-[#E4E6EB]">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                    Campaign
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-[#65676B]">
                    Budget
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-[#65676B]">
                    Spent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((t) => (
                  <tr
                    key={t.id}
                    className="border-b border-[#E4E6EB] hover:bg-[#F7F8FA] transition-colors"
                  >
                    <td className="px-6 py-4 text-sm text-[#65676B]">
                      {new Date(t.date).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </td>
                    <td className="px-6 py-4 text-sm text-[#050505]">
                      {t.description}
                    </td>
                    <td className="px-6 py-4 text-sm text-[#050505] text-right font-medium">
                      ${(Math.abs(t.amount) / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 text-sm text-[#050505] text-right">
                      ${(t.spent / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium border ${
                          t.status === "Active"
                            ? "bg-green-100 text-green-700 border-green-200"
                            : t.status === "Draft"
                            ? "bg-gray-100 text-gray-700 border-gray-200"
                            : t.status === "Exhausted"
                            ? "bg-yellow-100 text-yellow-700 border-yellow-200"
                            : "bg-blue-100 text-blue-700 border-blue-200"
                        }`}
                      >
                        {t.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Stripe Integration Note */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200">
        <div className="text-sm text-blue-900">
          <span className="font-medium">Payment processing:</span>{" "}
          Campaign funding is handled via Stripe Checkout. When you launch a campaign, you'll be redirected to Stripe to complete payment.
        </div>
      </div>
    </div>
  );
}
