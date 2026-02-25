import { Upload, Copy, Plus, Trash2 } from "lucide-react";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";

const teamMembers = [
  {
    id: 1,
    name: "Sarah Johnson",
    email: "sarah.johnson@acmeenergy.com",
    role: "Admin",
  },
  {
    id: 2,
    name: "Michael Chen",
    email: "michael.chen@acmeenergy.com",
    role: "Admin",
  },
  {
    id: 3,
    name: "Emma Williams",
    email: "emma.williams@acmeenergy.com",
    role: "Viewer",
  },
  {
    id: 4,
    name: "David Martinez",
    email: "david.martinez@acmeenergy.com",
    role: "Viewer",
  },
];

export function Settings() {
  return (
    <div className="p-8 max-w-5xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[#050505]">Settings</h1>
        <p className="text-sm text-[#65676B] mt-1">
          Manage your organization settings and team
        </p>
      </div>

      {/* Organization Settings */}
      <div className="bg-white border border-[#E4E6EB] p-6 mb-6">
        <h2 className="text-sm font-semibold text-[#050505] mb-6">
          Organization
        </h2>

        <div className="space-y-6">
          <div>
            <Label htmlFor="orgName">Organization Name</Label>
            <Input
              id="orgName"
              defaultValue="Acme Energy Corp"
              className="mt-1.5"
            />
          </div>

          <div>
            <Label>Organization Logo</Label>
            <div className="mt-1.5 flex items-center gap-4">
              <div className="w-20 h-20 bg-[#F7F8FA] border border-[#E4E6EB] rounded flex items-center justify-center">
                <span className="text-2xl font-bold text-[#1877F2]">A</span>
              </div>
              <button className="inline-flex items-center gap-2 px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors">
                <Upload className="w-4 h-4" />
                Upload New Logo
              </button>
            </div>
            <p className="text-xs text-[#65676B] mt-2">
              Recommended size: 200x200px. Max file size: 2MB.
            </p>
          </div>

          <div>
            <Label htmlFor="primaryEmail">Primary Contact Email</Label>
            <Input
              id="primaryEmail"
              type="email"
              defaultValue="contact@acmeenergy.com"
              className="mt-1.5"
            />
          </div>

          <div>
            <Label htmlFor="billingEmail">Billing Email</Label>
            <Input
              id="billingEmail"
              type="email"
              defaultValue="billing@acmeenergy.com"
              className="mt-1.5"
            />
          </div>

          <div className="pt-4 border-t border-[#E4E6EB]">
            <button className="px-4 py-2 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors">
              Save Changes
            </button>
          </div>
        </div>
      </div>

      {/* Team Members */}
      <div className="bg-white border border-[#E4E6EB] mb-6">
        <div className="px-6 py-4 border-b border-[#E4E6EB] flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[#050505]">Team Members</h2>
          <button className="inline-flex items-center gap-2 px-4 py-2 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors">
            <Plus className="w-4 h-4" />
            Invite Member
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#F7F8FA] border-b border-[#E4E6EB]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-[#65676B]">
                  Role
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-[#65676B]">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {teamMembers.map((member) => (
                <tr
                  key={member.id}
                  className="border-b border-[#E4E6EB] hover:bg-[#F7F8FA] transition-colors"
                >
                  <td className="px-6 py-4 text-sm text-[#050505]">
                    {member.name}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#65676B]">
                    {member.email}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium border ${
                        member.role === "Admin"
                          ? "bg-blue-100 text-blue-700 border-blue-200"
                          : "bg-gray-100 text-gray-700 border-gray-200"
                      }`}
                    >
                      {member.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button className="inline-flex items-center gap-1 text-sm text-red-600 hover:text-red-700">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* API Keys */}
      <div className="bg-white border border-[#E4E6EB] p-6">
        <h2 className="text-sm font-semibold text-[#050505] mb-6">API Keys</h2>

        <div className="space-y-4">
          <div>
            <Label>Production API Key</Label>
            <div className="mt-1.5 flex items-center gap-2">
              <Input
                value="sk_live_••••••••••••••••••••••••4f3a"
                readOnly
                className="font-mono text-sm"
              />
              <button className="px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors flex items-center gap-2 whitespace-nowrap">
                <Copy className="w-4 h-4" />
                Copy
              </button>
            </div>
            <p className="text-xs text-[#65676B] mt-2">
              Last used: February 23, 2026 at 2:34 PM
            </p>
          </div>

          <div>
            <Label>Test API Key</Label>
            <div className="mt-1.5 flex items-center gap-2">
              <Input
                value="sk_test_••••••••••••••••••••••••8b2c"
                readOnly
                className="font-mono text-sm"
              />
              <button className="px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors flex items-center gap-2 whitespace-nowrap">
                <Copy className="w-4 h-4" />
                Copy
              </button>
            </div>
            <p className="text-xs text-[#65676B] mt-2">
              Last used: February 22, 2026 at 11:15 AM
            </p>
          </div>

          <div className="pt-4">
            <button className="inline-flex items-center gap-2 px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors">
              <Plus className="w-4 h-4" />
              Generate New Key
            </button>
          </div>
        </div>

        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200">
          <div className="text-sm text-yellow-900">
            <span className="font-medium">Important:</span> Keep your API keys
            secure and never share them publicly. If you suspect a key has been
            compromised, regenerate it immediately.
          </div>
        </div>
      </div>
    </div>
  );
}
