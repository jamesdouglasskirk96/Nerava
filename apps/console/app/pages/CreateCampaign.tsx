import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronRight, Plus, X, Calendar, Loader2 } from "lucide-react";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Switch } from "../components/ui/switch";
import {
  createCampaign,
  activateCampaign,
  type CreateCampaignInput,
} from "../services/api";

const steps = [
  { number: 1, name: "Details" },
  { number: 2, name: "Targeting" },
  { number: 3, name: "Budget" },
  { number: 4, name: "Review" },
];

const campaignTypes = [
  "utilization_boost",
  "off_peak_shift",
  "new_driver_acquisition",
  "repeat_visit",
  "corridor",
  "custom",
];

const campaignTypeLabels: Record<string, string> = {
  utilization_boost: "Utilization Boost",
  off_peak_shift: "Off-Peak Shift",
  new_driver_acquisition: "New Driver Acquisition",
  repeat_visit: "Repeat Visit",
  corridor: "Corridor Campaign",
  custom: "Custom",
};

interface Rule {
  id: string;
  type: string;
  value: string;
}

export function CreateCampaign() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Details
  const [campaignName, setCampaignName] = useState("");
  const [sponsorName, setSponsorName] = useState("");
  const [sponsorEmail, setSponsorEmail] = useState("");
  const [campaignType, setCampaignType] = useState("");
  const [description, setDescription] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [runUntilExhausted, setRunUntilExhausted] = useState(false);

  // Step 2: Targeting
  const [rules, setRules] = useState<Rule[]>([]);
  const [minDuration, setMinDuration] = useState("15");
  const [chargerNetworks, setChargerNetworks] = useState("");
  const [timeStart, setTimeStart] = useState("");
  const [timeEnd, setTimeEnd] = useState("");
  const [maxPerDriverPerDay, setMaxPerDriverPerDay] = useState("");
  const [maxPerDriverPerCampaign, setMaxPerDriverPerCampaign] = useState("");

  // Step 3: Budget
  const [totalBudget, setTotalBudget] = useState("");
  const [costPerSession, setCostPerSession] = useState("");
  const [maxSessions, setMaxSessions] = useState("");
  const [autoRenew, setAutoRenew] = useState(false);
  const [autoRenewBudget, setAutoRenewBudget] = useState("");

  const addRule = () => {
    setRules([
      ...rules,
      { id: Date.now().toString(), type: "", value: "" },
    ]);
  };

  const removeRule = (id: string) => {
    setRules(rules.filter((rule) => rule.id !== id));
  };

  const budgetCents = totalBudget ? Math.round(parseFloat(totalBudget) * 100) : 0;
  const costCents = costPerSession
    ? Math.round(parseFloat(costPerSession) * 100)
    : 0;
  const estimatedSessions =
    budgetCents && costCents ? Math.floor(budgetCents / costCents) : 0;

  function buildInput(): CreateCampaignInput {
    const input: CreateCampaignInput = {
      sponsor_name: sponsorName || "Default Sponsor",
      sponsor_email: sponsorEmail || undefined,
      name: campaignName,
      description: description || undefined,
      campaign_type: campaignType || "custom",
      budget_cents: budgetCents,
      cost_per_session_cents: costCents,
      start_date: startDate || new Date().toISOString().split("T")[0],
      end_date: runUntilExhausted ? undefined : endDate || undefined,
      auto_renew: autoRenew,
      auto_renew_budget_cents: autoRenewBudget
        ? Math.round(parseFloat(autoRenewBudget) * 100)
        : undefined,
      max_sessions: maxSessions ? parseInt(maxSessions) : undefined,
      rules: {
        min_duration_minutes: parseInt(minDuration) || 15,
        charger_networks: chargerNetworks
          ? chargerNetworks.split(",").map((s) => s.trim())
          : undefined,
        time_start: timeStart || undefined,
        time_end: timeEnd || undefined,
      },
      caps: {
        per_day: maxPerDriverPerDay ? parseInt(maxPerDriverPerDay) : undefined,
        per_campaign: maxPerDriverPerCampaign
          ? parseInt(maxPerDriverPerCampaign)
          : undefined,
      },
    };
    return input;
  }

  async function handleSaveDraft() {
    try {
      setSubmitting(true);
      setError(null);
      const input = buildInput();
      await createCampaign(input);
      navigate("/campaigns");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save campaign");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLaunch() {
    try {
      setSubmitting(true);
      setError(null);
      const input = buildInput();
      const { campaign } = await createCampaign(input);
      await activateCampaign(campaign.id);
      navigate("/campaigns");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to launch campaign");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[#050505]">
          Create Campaign
        </h1>
        <p className="text-sm text-[#65676B] mt-1">
          Set up a new incentive campaign
        </p>
      </div>

      {/* Step Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between max-w-2xl">
          {steps.map((step, index) => (
            <div key={step.number} className="flex items-center flex-1">
              <div className="flex items-center gap-3">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    currentStep >= step.number
                      ? "bg-[#1877F2] text-white"
                      : "bg-[#E4E6EB] text-[#65676B]"
                  }`}
                >
                  {step.number}
                </div>
                <span
                  className={`text-sm font-medium ${
                    currentStep >= step.number
                      ? "text-[#050505]"
                      : "text-[#65676B]"
                  }`}
                >
                  {step.name}
                </span>
              </div>
              {index < steps.length - 1 && (
                <ChevronRight className="w-5 h-5 text-[#E4E6EB] mx-4 flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 mb-4 bg-red-50 border border-red-200 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Step Content */}
      <div className="bg-white border border-[#E4E6EB] p-8">
        {currentStep === 1 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-[#050505]">
              Campaign Details
            </h2>

            <div>
              <Label htmlFor="campaignName">Campaign Name</Label>
              <Input
                id="campaignName"
                value={campaignName}
                onChange={(e) => setCampaignName(e.target.value)}
                placeholder="e.g. Austin Off-Peak Boost"
                className="mt-1.5"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="sponsorName">Sponsor Name</Label>
                <Input
                  id="sponsorName"
                  value={sponsorName}
                  onChange={(e) => setSponsorName(e.target.value)}
                  placeholder="e.g. Acme Energy Corp"
                  className="mt-1.5"
                />
              </div>
              <div>
                <Label htmlFor="sponsorEmail">Sponsor Email (Optional)</Label>
                <Input
                  id="sponsorEmail"
                  type="email"
                  value={sponsorEmail}
                  onChange={(e) => setSponsorEmail(e.target.value)}
                  placeholder="contact@sponsor.com"
                  className="mt-1.5"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="campaignType">Campaign Type</Label>
              <Select value={campaignType} onValueChange={setCampaignType}>
                <SelectTrigger className="mt-1.5">
                  <SelectValue placeholder="Select campaign type" />
                </SelectTrigger>
                <SelectContent>
                  {campaignTypes.map((type) => (
                    <SelectItem key={type} value={type}>
                      {campaignTypeLabels[type]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the campaign objectives and target behavior"
                className="mt-1.5"
                rows={4}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="startDate">Start Date</Label>
                <div className="relative mt-1.5">
                  <Input
                    id="startDate"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                  <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#65676B] pointer-events-none" />
                </div>
              </div>
              <div>
                <Label htmlFor="endDate">End Date (Optional)</Label>
                <div className="relative mt-1.5">
                  <Input
                    id="endDate"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    disabled={runUntilExhausted}
                  />
                  <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#65676B] pointer-events-none" />
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Switch
                id="runUntilExhausted"
                checked={runUntilExhausted}
                onCheckedChange={setRunUntilExhausted}
              />
              <Label htmlFor="runUntilExhausted" className="cursor-pointer">
                Run until budget exhausted
              </Label>
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-[#050505]">
              Targeting Rules
            </h2>
            <p className="text-sm text-[#65676B]">
              Define which charging sessions qualify for this campaign
            </p>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="minDuration">
                  Minimum Duration (minutes)
                </Label>
                <Input
                  id="minDuration"
                  type="number"
                  value={minDuration}
                  onChange={(e) => setMinDuration(e.target.value)}
                  placeholder="15"
                  className="mt-1.5"
                />
                <p className="text-xs text-[#65676B] mt-1">
                  Required. Sessions shorter than this are rejected.
                </p>
              </div>
              <div>
                <Label htmlFor="chargerNetworks">
                  Charging Networks (comma-separated)
                </Label>
                <Input
                  id="chargerNetworks"
                  value={chargerNetworks}
                  onChange={(e) => setChargerNetworks(e.target.value)}
                  placeholder="Tesla Supercharger, ChargePoint"
                  className="mt-1.5"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="timeStart">Time Window Start</Label>
                <Input
                  id="timeStart"
                  type="time"
                  value={timeStart}
                  onChange={(e) => setTimeStart(e.target.value)}
                  className="mt-1.5"
                />
              </div>
              <div>
                <Label htmlFor="timeEnd">Time Window End</Label>
                <Input
                  id="timeEnd"
                  type="time"
                  value={timeEnd}
                  onChange={(e) => setTimeEnd(e.target.value)}
                  className="mt-1.5"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="maxPerDay">
                  Max Grants Per Driver Per Day
                </Label>
                <Input
                  id="maxPerDay"
                  type="number"
                  value={maxPerDriverPerDay}
                  onChange={(e) => setMaxPerDriverPerDay(e.target.value)}
                  placeholder="Leave empty for no cap"
                  className="mt-1.5"
                />
              </div>
              <div>
                <Label htmlFor="maxPerCampaign">
                  Max Grants Per Driver Per Campaign
                </Label>
                <Input
                  id="maxPerCampaign"
                  type="number"
                  value={maxPerDriverPerCampaign}
                  onChange={(e) => setMaxPerDriverPerCampaign(e.target.value)}
                  placeholder="Leave empty for no cap"
                  className="mt-1.5"
                />
              </div>
            </div>

            {/* Additional custom rules */}
            {rules.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-[#050505]">
                  Additional Rules
                </h3>
                {rules.map((rule) => (
                  <div
                    key={rule.id}
                    className="flex items-start gap-3 p-4 border border-[#E4E6EB] bg-[#F7F8FA]"
                  >
                    <div className="flex-1 grid grid-cols-2 gap-3">
                      <div>
                        <Label className="text-xs">Rule Type</Label>
                        <Select value={rule.type} onValueChange={() => {}}>
                          <SelectTrigger className="mt-1">
                            <SelectValue placeholder="Select type" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="charger_ids">
                              Specific Chargers
                            </SelectItem>
                            <SelectItem value="zone_ids">Zone IDs</SelectItem>
                            <SelectItem value="geo_radius">
                              Geographic Radius
                            </SelectItem>
                            <SelectItem value="connector_types">
                              Connector Types
                            </SelectItem>
                            <SelectItem value="driver_allowlist">
                              Driver Allowlist
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label className="text-xs">Value</Label>
                        <Input
                          value={rule.value}
                          className="mt-1"
                          placeholder="Enter value"
                          readOnly
                        />
                      </div>
                    </div>
                    <button
                      onClick={() => removeRule(rule.id)}
                      className="mt-6 p-1.5 hover:bg-[#E4E6EB] rounded transition-colors"
                    >
                      <X className="w-4 h-4 text-[#65676B]" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={addRule}
              className="inline-flex items-center gap-2 px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Custom Rule
            </button>
          </div>
        )}

        {currentStep === 3 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-[#050505]">
              Budget & Pricing
            </h2>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="totalBudget">Total Budget</Label>
                <div className="relative mt-1.5">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#65676B]">
                    $
                  </span>
                  <Input
                    id="totalBudget"
                    type="number"
                    value={totalBudget}
                    onChange={(e) => setTotalBudget(e.target.value)}
                    placeholder="25000"
                    className="pl-7"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="costPerSession">Cost Per Session</Label>
                <div className="relative mt-1.5">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#65676B]">
                    $
                  </span>
                  <Input
                    id="costPerSession"
                    type="number"
                    step="0.01"
                    value={costPerSession}
                    onChange={(e) => setCostPerSession(e.target.value)}
                    placeholder="2.00"
                    className="pl-7"
                  />
                </div>
              </div>
            </div>

            {estimatedSessions > 0 && (
              <div className="p-4 bg-[#F7F8FA] border border-[#E4E6EB]">
                <div className="text-xs text-[#65676B] mb-1">
                  Estimated Sessions
                </div>
                <div className="text-2xl font-semibold text-[#050505]">
                  {estimatedSessions.toLocaleString()}
                </div>
                <div className="text-xs text-[#65676B] mt-1">
                  Based on ${totalBudget} budget at ${costPerSession} per
                  session
                </div>
              </div>
            )}

            <div>
              <Label htmlFor="maxSessions">
                Maximum Sessions Cap (Optional)
              </Label>
              <Input
                id="maxSessions"
                type="number"
                value={maxSessions}
                onChange={(e) => setMaxSessions(e.target.value)}
                placeholder="Leave empty for no cap"
                className="mt-1.5"
              />
            </div>

            <div className="space-y-3 pt-4 border-t border-[#E4E6EB]">
              <div className="flex items-center gap-2">
                <Switch
                  id="autoRenew"
                  checked={autoRenew}
                  onCheckedChange={setAutoRenew}
                />
                <Label htmlFor="autoRenew" className="cursor-pointer">
                  Auto-renew monthly
                </Label>
              </div>
              {autoRenew && (
                <div className="ml-11">
                  <Label htmlFor="monthlyBudget">Monthly Budget</Label>
                  <div className="relative mt-1.5">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#65676B]">
                      $
                    </span>
                    <Input
                      id="monthlyBudget"
                      type="number"
                      value={autoRenewBudget}
                      onChange={(e) => setAutoRenewBudget(e.target.value)}
                      placeholder="25000"
                      className="pl-7"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {currentStep === 4 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-[#050505]">
              Review & Launch
            </h2>
            <p className="text-sm text-[#65676B]">
              Review your campaign settings before launching
            </p>

            <div className="space-y-4">
              <div className="p-4 border border-[#E4E6EB]">
                <h3 className="text-sm font-semibold text-[#050505] mb-3">
                  Campaign Details
                </h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-[#65676B]">Name:</span>{" "}
                    <span className="text-[#050505]">
                      {campaignName || "—"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#65676B]">Sponsor:</span>{" "}
                    <span className="text-[#050505]">
                      {sponsorName || "—"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#65676B]">Type:</span>{" "}
                    <span className="text-[#050505]">
                      {campaignType
                        ? campaignTypeLabels[campaignType]
                        : "—"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#65676B]">Start Date:</span>{" "}
                    <span className="text-[#050505]">{startDate || "—"}</span>
                  </div>
                  <div>
                    <span className="text-[#65676B]">End Date:</span>{" "}
                    <span className="text-[#050505]">
                      {runUntilExhausted
                        ? "Until exhausted"
                        : endDate || "—"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-4 border border-[#E4E6EB]">
                <h3 className="text-sm font-semibold text-[#050505] mb-3">
                  Targeting Rules
                </h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-[#65676B]">Min Duration:</span>{" "}
                    <span className="text-[#050505]">
                      {minDuration} minutes
                    </span>
                  </div>
                  {chargerNetworks && (
                    <div>
                      <span className="text-[#65676B]">Networks:</span>{" "}
                      <span className="text-[#050505]">{chargerNetworks}</span>
                    </div>
                  )}
                  {timeStart && timeEnd && (
                    <div>
                      <span className="text-[#65676B]">Time Window:</span>{" "}
                      <span className="text-[#050505]">
                        {timeStart} - {timeEnd}
                      </span>
                    </div>
                  )}
                  {maxPerDriverPerDay && (
                    <div>
                      <span className="text-[#65676B]">Max/Driver/Day:</span>{" "}
                      <span className="text-[#050505]">
                        {maxPerDriverPerDay}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="p-4 border border-[#E4E6EB]">
                <h3 className="text-sm font-semibold text-[#050505] mb-3">
                  Budget & Pricing
                </h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-[#65676B]">Total Budget:</span>{" "}
                    <span className="text-[#050505]">
                      ${totalBudget || "—"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#65676B]">Cost Per Session:</span>{" "}
                    <span className="text-[#050505]">
                      ${costPerSession || "—"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#65676B]">
                      Estimated Sessions:
                    </span>{" "}
                    <span className="text-[#050505]">
                      {estimatedSessions.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#65676B]">Auto-renew:</span>{" "}
                    <span className="text-[#050505]">
                      {autoRenew ? "Yes" : "No"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-[#E4E6EB]">
          <button
            onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
            disabled={currentStep === 1}
            className="px-4 py-2 text-sm font-medium text-[#65676B] hover:text-[#050505] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Back
          </button>
          <div className="flex items-center gap-3">
            {currentStep === 4 && (
              <button
                onClick={handleSaveDraft}
                disabled={submitting}
                className="px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors disabled:opacity-50"
              >
                {submitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  "Save as Draft"
                )}
              </button>
            )}
            {currentStep < 4 ? (
              <button
                onClick={() => setCurrentStep(Math.min(4, currentStep + 1))}
                className="px-4 py-2 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors"
              >
                Continue
              </button>
            ) : (
              <button
                onClick={handleLaunch}
                disabled={submitting || !campaignName || !totalBudget || !costPerSession}
                className="px-4 py-2 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors disabled:opacity-50"
              >
                {submitting ? (
                  <Loader2 className="w-4 h-4 animate-spin inline mr-2" />
                ) : null}
                Launch Campaign
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
