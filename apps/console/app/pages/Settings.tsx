import { useState, useEffect } from "react";
import { Copy, Plus, Check, User } from "lucide-react";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";

function getLoggedInEmail(): string | null {
  return localStorage.getItem("user_email") || null;
}

export function Settings() {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    setUserEmail(getLoggedInEmail());
  }, []);

  function copyToClipboard(text: string, key: string) {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  }

  return (
    <div className="p-8 max-w-5xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[#050505]">Settings</h1>
        <p className="text-sm text-[#65676B] mt-1">
          Manage your account and organization settings
        </p>
      </div>

      {/* Account Info */}
      <div className="bg-white border border-[#E4E6EB] p-6 mb-6">
        <h2 className="text-sm font-semibold text-[#050505] mb-6">
          Account
        </h2>

        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-[#F7F8FA] border border-[#E4E6EB] rounded-full flex items-center justify-center">
              <User className="w-6 h-6 text-[#1877F2]" />
            </div>
            <div>
              <div className="text-sm font-medium text-[#050505]">
                {userEmail || "Signed in"}
              </div>
              <div className="text-xs text-[#65676B] mt-0.5">
                Sponsor account
              </div>
            </div>
          </div>

          <div className="p-4 bg-[#F7F8FA] border border-[#E4E6EB]">
            <p className="text-sm text-[#65676B]">
              Organization profile settings and branding customization are coming soon.
            </p>
          </div>
        </div>
      </div>

      {/* Team Management - Coming Soon */}
      <div className="bg-white border border-[#E4E6EB] mb-6">
        <div className="px-6 py-4 border-b border-[#E4E6EB] flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[#050505]">Team Members</h2>
          <button
            disabled
            className="inline-flex items-center gap-2 px-4 py-2 bg-[#1877F2] text-white text-sm font-medium opacity-50 cursor-not-allowed"
          >
            <Plus className="w-4 h-4" />
            Invite Member
          </button>
        </div>
        <div className="px-6 py-8 text-center">
          <p className="text-sm text-[#65676B] mb-1">
            Team management is coming soon.
          </p>
          <p className="text-xs text-[#65676B]">
            You'll be able to invite team members and assign roles.
          </p>
        </div>
      </div>

      {/* API Keys */}
      <div className="bg-white border border-[#E4E6EB] p-6">
        <h2 className="text-sm font-semibold text-[#050505] mb-6">API Keys</h2>

        <div className="space-y-4">
          <div className="p-4 bg-[#F7F8FA] border border-[#E4E6EB]">
            <p className="text-sm text-[#050505] mb-2">
              Use API keys to integrate Nerava campaigns with your platform via the Partner API.
            </p>
            <p className="text-xs text-[#65676B]">
              Contact <span className="font-medium">support@nerava.network</span> to request API access.
            </p>
          </div>

          <div>
            <Label>API Base URL</Label>
            <div className="mt-1.5 flex items-center gap-2">
              <Input
                value="https://api.nerava.network/v1/partners"
                readOnly
                className="font-mono text-sm"
              />
              <button
                onClick={() => copyToClipboard("https://api.nerava.network/v1/partners", "url")}
                className="px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors flex items-center gap-2 whitespace-nowrap"
              >
                {copiedKey === "url" ? (
                  <Check className="w-4 h-4 text-green-600" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
                {copiedKey === "url" ? "Copied" : "Copy"}
              </button>
            </div>
          </div>

          <div>
            <Label>API Documentation</Label>
            <p className="text-sm text-[#65676B] mt-1.5">
              See the{" "}
              <a
                href="https://api.nerava.network/docs#/Partner%20API"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[#1877F2] hover:underline"
              >
                Partner API documentation
              </a>
              {" "}for endpoints, authentication, and usage examples.
            </p>
          </div>
        </div>

        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200">
          <div className="text-sm text-yellow-900">
            <span className="font-medium">Security:</span> Keep your API keys
            secure and never share them publicly. Keys use the format{" "}
            <code className="text-xs bg-yellow-100 px-1 py-0.5">nrv_pk_*</code>{" "}
            and are scoped per environment.
          </div>
        </div>
      </div>
    </div>
  );
}
