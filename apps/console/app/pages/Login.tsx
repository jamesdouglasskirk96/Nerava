import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { setToken, setRefreshToken } from "../services/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

interface LoginProps {
  onLogin: () => void;
}

export function Login({ onLogin }: LoginProps) {
  const [mode, setMode] = useState<"email-otp" | "password">("email-otp");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"email" | "code">("email");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSendCode() {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API_BASE}/v1/console/auth/email-otp/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
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
      const res = await fetch(`${API_BASE}/v1/console/auth/email-otp/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error: ${res.status}`);
      }
      const data = await res.json();
      setToken(data.access_token);
      if (data.refresh_token) setRefreshToken(data.refresh_token);
      localStorage.setItem("user_email", email);
      onLogin();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to verify code");
    } finally {
      setLoading(false);
    }
  }

  async function handlePasswordLogin() {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API_BASE}/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error: ${res.status}`);
      }
      const data = await res.json();
      setToken(data.access_token);
      localStorage.setItem("user_email", email);
      onLogin();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Login failed");
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
            {mode === "email-otp"
              ? step === "email"
                ? "Enter your email to receive a verification code"
                : "Enter the 6-digit code sent to your email"
              : "Sign in with your email and password"}
          </p>

          {mode === "email-otp" && step === "email" && (
            <div className="p-3 mb-4 bg-blue-50 border border-blue-200 text-xs text-blue-800">
              New to Nerava? Your sponsor account will be created automatically when you verify your email.
            </div>
          )}

          {error && (
            <div className="p-3 mb-4 bg-red-50 border border-red-200 text-sm text-red-700">
              {error}
            </div>
          )}

          {mode === "email-otp" ? (
            step === "email" ? (
              <div className="space-y-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    className="mt-1.5"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && email) handleSendCode();
                    }}
                  />
                </div>
                <button
                  onClick={handleSendCode}
                  disabled={loading || !email}
                  className="w-full px-4 py-2.5 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  Send Code
                </button>
                <button
                  onClick={() => {
                    setMode("password");
                    setError(null);
                  }}
                  className="w-full text-sm text-[#65676B] hover:text-[#050505]"
                >
                  Sign in with password instead
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-[#65676B]">
                  Code sent to <strong>{email}</strong>
                </p>
                <div>
                  <Label htmlFor="code">Verification Code</Label>
                  <Input
                    id="code"
                    type="text"
                    inputMode="numeric"
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    placeholder="123456"
                    className="mt-1.5"
                    maxLength={6}
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && code.length === 6) handleVerifyCode();
                    }}
                  />
                </div>
                <button
                  onClick={handleVerifyCode}
                  disabled={loading || code.length !== 6}
                  className="w-full px-4 py-2.5 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  Verify & Sign In
                </button>
                <div className="flex justify-between">
                  <button
                    onClick={() => {
                      setStep("email");
                      setCode("");
                      setError(null);
                    }}
                    className="text-sm text-[#65676B] hover:text-[#050505]"
                  >
                    Use a different email
                  </button>
                  <button
                    onClick={() => {
                      setCode("");
                      setError(null);
                      handleSendCode();
                    }}
                    disabled={loading}
                    className="text-sm text-[#1877F2] hover:text-[#166FE5]"
                  >
                    Resend code
                  </button>
                </div>
              </div>
            )
          ) : (
            <div className="space-y-4">
              <div>
                <Label htmlFor="email-pw">Email</Label>
                <Input
                  id="email-pw"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="mt-1.5"
                />
              </div>
              <div>
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="mt-1.5"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && email && password) handlePasswordLogin();
                  }}
                />
              </div>
              <button
                onClick={handlePasswordLogin}
                disabled={loading || !email || !password}
                className="w-full px-4 py-2.5 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Sign In
              </button>
              <button
                onClick={() => {
                  setMode("email-otp");
                  setStep("email");
                  setError(null);
                }}
                className="w-full text-sm text-[#65676B] hover:text-[#050505]"
              >
                Sign in with email code instead
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
