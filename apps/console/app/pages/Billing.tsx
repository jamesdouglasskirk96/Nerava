import { Plus, CreditCard, Download } from "lucide-react";

const transactions = [
  {
    id: 1,
    date: "2026-02-20",
    description: "Campaign Funding - Austin Off-Peak Boost",
    amount: -5000,
    status: "Completed",
  },
  {
    id: 2,
    date: "2026-02-15",
    description: "Auto-renewal - Tesla Supercharger Network Q1",
    amount: -8000,
    status: "Completed",
  },
  {
    id: 3,
    date: "2026-02-10",
    description: "Account Balance Top-up",
    amount: 50000,
    status: "Completed",
  },
  {
    id: 4,
    date: "2026-02-05",
    description: "Campaign Funding - Weekend Corridor Campaign",
    amount: -3000,
    status: "Completed",
  },
  {
    id: 5,
    date: "2026-02-01",
    description: "Campaign Funding - New Driver Acquisition - West",
    amount: -2000,
    status: "Completed",
  },
  {
    id: 6,
    date: "2026-01-28",
    description: "Account Balance Top-up",
    amount: 100000,
    status: "Completed",
  },
  {
    id: 7,
    date: "2026-01-25",
    description: "Campaign Funding - Evening Rush Hour Incentive",
    amount: -6000,
    status: "Completed",
  },
  {
    id: 8,
    date: "2026-01-20",
    description: "Campaign Funding - Downtown Utilization Push",
    amount: -4500,
    status: "Completed",
  },
  {
    id: 9,
    date: "2026-01-15",
    description: "Auto-renewal - Austin Off-Peak Boost",
    amount: -10000,
    status: "Pending",
  },
  {
    id: 10,
    date: "2026-01-10",
    description: "Account Balance Top-up",
    amount: 75000,
    status: "Completed",
  },
];

export function Billing() {
  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[#050505]">Billing</h1>
        <p className="text-sm text-[#65676B] mt-1">
          Manage your account balance and payment methods
        </p>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-8">
        {/* Balance Card */}
        <div className="bg-white border border-[#E4E6EB] p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="text-xs text-[#65676B] mb-1">
                Current Balance
              </div>
              <div className="text-3xl font-semibold text-[#050505]">
                $127,450
              </div>
            </div>
            <div className="w-12 h-12 bg-[#F7F8FA] rounded-full flex items-center justify-center">
              <CreditCard className="w-6 h-6 text-[#1877F2]" />
            </div>
          </div>
          <button className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors">
            <Plus className="w-4 h-4" />
            Add Funds
          </button>
        </div>

        {/* Payment Method */}
        <div className="col-span-2 bg-white border border-[#E4E6EB] p-6">
          <h2 className="text-sm font-semibold text-[#050505] mb-4">
            Payment Method
          </h2>
          <div className="flex items-center justify-between p-4 bg-[#F7F8FA] border border-[#E4E6EB]">
            <div className="flex items-center gap-4">
              <div className="w-12 h-8 bg-white border border-[#E4E6EB] rounded flex items-center justify-center">
                <CreditCard className="w-5 h-5 text-[#1877F2]" />
              </div>
              <div>
                <div className="text-sm font-medium text-[#050505]">
                  •••• •••• •••• 4242
                </div>
                <div className="text-xs text-[#65676B]">Expires 12/2027</div>
              </div>
            </div>
            <button className="text-sm text-[#1877F2] hover:underline">
              Update
            </button>
          </div>
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200">
            <div className="text-sm text-blue-900">
              <span className="font-medium">Auto-recharge enabled:</span> We'll
              automatically add $50,000 when your balance drops below $10,000
            </div>
          </div>
        </div>
      </div>

      {/* Transaction History */}
      <div className="bg-white border border-[#E4E6EB]">
        <div className="px-6 py-4 border-b border-[#E4E6EB]">
          <h2 className="text-sm font-semibold text-[#050505]">
            Transaction History
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#F7F8FA] border-b border-[#E4E6EB]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Description
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-[#65676B]">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Status
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-[#65676B]">
                  Receipt
                </th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction) => (
                <tr
                  key={transaction.id}
                  className="border-b border-[#E4E6EB] hover:bg-[#F7F8FA] transition-colors"
                >
                  <td className="px-6 py-4 text-sm text-[#65676B]">
                    {new Date(transaction.date).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#050505]">
                    {transaction.description}
                  </td>
                  <td
                    className={`px-6 py-4 text-sm font-semibold text-right ${
                      transaction.amount > 0
                        ? "text-green-600"
                        : "text-[#050505]"
                    }`}
                  >
                    {transaction.amount > 0 ? "+" : ""}$
                    {Math.abs(transaction.amount).toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium border ${
                        transaction.status === "Completed"
                          ? "bg-green-100 text-green-700 border-green-200"
                          : "bg-yellow-100 text-yellow-700 border-yellow-200"
                      }`}
                    >
                      {transaction.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    {transaction.status === "Completed" && (
                      <button className="inline-flex items-center gap-1 text-sm text-[#1877F2] hover:underline">
                        <Download className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 border-t border-[#E4E6EB] flex items-center justify-between">
          <div className="text-sm text-[#65676B]">Showing 1-10 of 147</div>
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
