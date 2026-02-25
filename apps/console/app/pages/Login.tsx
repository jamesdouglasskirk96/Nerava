import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { setToken } from "../services/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

interface LoginProps {
  onLogin: () => void;
}

export function Login({ onLogin }: LoginProps) {
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"phone" | "code">("phone");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSendCode() {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API_BASE}/v1/auth/otp/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: phone }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error: ${res.status}`);
      }
      setStep("code");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send code");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyCode() {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API_BASE}/v1/auth/otp/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: phone, code }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error: ${res.status}`);
      }
      const data = await res.json();
      setToken(data.access_token);
      onLogin();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to verify code");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F7F8FA]">
      <div className="w-full max-w-sm">
        <div className="bg-white border border-[#E4E6EB] p-8">
          {/* Logo */}
          <div className="flex items-center gap-2 mb-8">
            <div className="w-8 h-8 bg-[#1877F2] rounded flex items-center justify-center">
              <span className="text-white font-bold text-lg">N</span>
            </div>
            <span className="font-semibold text-[#050505]">
              Nerava Console
            </span>
          </div>

          <h1 className="text-xl font-semibold text-[#050505] mb-2">
            Sign in
          </h1>
          <p className="text-sm text-[#65676B] mb-6">
            {step === "phone"
              ? "Enter your phone number to get started"
              : "Enter the verification code sent to your phone"}
          </p>

          {error && (
            <div className="p-3 mb-4 bg-red-50 border border-red-200 text-sm text-red-700">
              {error}
            </div>
          )}

          {step === "phone" ? (
            <div className="space-y-4">
              <div>
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+1 (555) 123-4567"
                  className="mt-1.5"
                />
              </div>
              <button
                onClick={handleSendCode}
                disabled={loading || !phone}
                className="w-full px-4 py-2.5 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Send Code
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <Label htmlFor="code">Verification Code</Label>
                <Input
                  id="code"
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="123456"
                  className="mt-1.5"
                  maxLength={6}
                />
              </div>
              <button
                onClick={handleVerifyCode}
                disabled={loading || !code}
                className="w-full px-4 py-2.5 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Verify & Sign In
              </button>
              <button
                onClick={() => {
                  setStep("phone");
                  setCode("");
                  setError(null);
                }}
                className="w-full text-sm text-[#65676B] hover:text-[#050505]"
              >
                Use a different number
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
