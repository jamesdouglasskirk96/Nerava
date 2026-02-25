import { useState } from "react";
import { useNavigate } from "react-router";
import { ChevronRight, Plus, X, Calendar, MapPin } from "lucide-react";
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

const steps = [
  { number: 1, name: "Details" },
  { number: 2, name: "Targeting" },
  { number: 3, name: "Budget" },
  { number: 4, name: "Review" },
];

const campaignTypes = [
  "Utilization Boost",
  "Off-Peak Shift",
  "New Driver Acquisition",
  "Repeat Visit",
  "Corridor Campaign",
  "Custom",
];

interface Rule {
  id: string;
  type: string;
  operator: string;
  value: string;
}

export function CreateCampaign() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [campaignName, setCampaignName] = useState("");
  const [campaignType, setCampaignType] = useState("");
  const [description, setDescription] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [runUntilExhausted, setRunUntilExhausted] = useState(false);
  const [totalBudget, setTotalBudget] = useState("");
  const [costPerSession, setCostPerSession] = useState("");
  const [autoRenew, setAutoRenew] = useState(false);
  const [rules, setRules] = useState<Rule[]>([
    {
      id: "1",
      type: "Time of Day",
      operator: "is between",
      value: "10:00 PM - 6:00 AM",
    },
    {
      id: "2",
      type: "Geographic Zone",
      operator: "within",
      value: "Downtown Austin (2 mi radius)",
    },
    {
      id: "3",
      type: "Charging Network",
      operator: "is",
      value: "Tesla Supercharger, ChargePoint",
    },
  ]);

  const addRule = () => {
    setRules([
      ...rules,
      { id: Date.now().toString(), type: "", operator: "", value: "" },
    ]);
  };

  const removeRule = (id: string) => {
    setRules(rules.filter((rule) => rule.id !== id));
  };

  const estimatedSessions =
    totalBudget && costPerSession
      ? Math.floor(parseFloat(totalBudget) / parseFloat(costPerSession))
      : 0;

  const handleLaunch = () => {
    // In a real app, this would submit to the backend
    navigate("/campaigns");
  };

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

            <div>
              <Label htmlFor="campaignType">Campaign Type</Label>
              <Select value={campaignType} onValueChange={setCampaignType}>
                <SelectTrigger className="mt-1.5">
                  <SelectValue placeholder="Select campaign type" />
                </SelectTrigger>
                <SelectContent>
                  {campaignTypes.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
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

            <div className="space-y-3">
              {rules.map((rule, index) => (
                <div
                  key={rule.id}
                  className="flex items-start gap-3 p-4 border border-[#E4E6EB] bg-[#F7F8FA]"
                >
                  <div className="flex-1 grid grid-cols-3 gap-3">
                    <div>
                      <Label className="text-xs">Rule Type</Label>
                      <Select value={rule.type} onValueChange={() => {}}>
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Charger Location">
                            Charger Location
                          </SelectItem>
                          <SelectItem value="Charging Network">
                            Charging Network
                          </SelectItem>
                          <SelectItem value="Geographic Zone">
                            Geographic Zone
                          </SelectItem>
                          <SelectItem value="Time of Day">
                            Time of Day
                          </SelectItem>
                          <SelectItem value="Day of Week">
                            Day of Week
                          </SelectItem>
                          <SelectItem value="Minimum Duration">
                            Minimum Duration
                          </SelectItem>
                          <SelectItem value="Connector Type">
                            Connector Type
                          </SelectItem>
                          <SelectItem value="Driver Segment">
                            Driver Segment
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-xs">Operator</Label>
                      <Select value={rule.operator} onValueChange={() => {}}>
                        <SelectTrigger className="mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="is">is</SelectItem>
                          <SelectItem value="is not">is not</SelectItem>
                          <SelectItem value="is between">is between</SelectItem>
                          <SelectItem value="is greater than">
                            is greater than
                          </SelectItem>
                          <SelectItem value="within">within</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-xs">Value</Label>
                      <Input value={rule.value} className="mt-1" readOnly />
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

            <button
              onClick={addRule}
              className="inline-flex items-center gap-2 px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Rule
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
                    <span className="text-[#65676B]">Type:</span>{" "}
                    <span className="text-[#050505]">
                      {campaignType || "—"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#65676B]">Start Date:</span>{" "}
                    <span className="text-[#050505]">{startDate || "—"}</span>
                  </div>
                  <div>
                    <span className="text-[#65676B]">End Date:</span>{" "}
                    <span className="text-[#050505]">
                      {runUntilExhausted ? "Until exhausted" : endDate || "—"}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-4 border border-[#E4E6EB]">
                <h3 className="text-sm font-semibold text-[#050505] mb-3">
                  Targeting Rules
                </h3>
                <div className="space-y-2">
                  {rules.map((rule) => (
                    <div
                      key={rule.id}
                      className="text-sm px-3 py-2 bg-[#F7F8FA] text-[#050505]"
                    >
                      {rule.type} {rule.operator} {rule.value}
                    </div>
                  ))}
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
                    <span className="text-[#65676B]">Estimated Sessions:</span>{" "}
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
              <button className="px-4 py-2 border border-[#E4E6EB] text-sm font-medium text-[#050505] hover:bg-[#F7F8FA] transition-colors">
                Save as Draft
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
                className="px-4 py-2 bg-[#1877F2] text-white text-sm font-medium hover:bg-[#166FE5] transition-colors"
              >
                Launch Campaign
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
