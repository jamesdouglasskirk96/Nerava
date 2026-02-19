import { Coffee, Utensils, Laptop, X } from "lucide-react";
import { useState } from "react";

export type RefuelIntent = 'eat' | 'work' | 'quick-stop';

export interface RefuelDetails {
  intent: RefuelIntent;
  partySize?: number;
  needsPowerOutlet?: boolean;
  isToGo?: boolean;
}

interface RefuelIntentModalProps {
  merchantName: string;
  onConfirm: (details: RefuelDetails) => void;
  onClose: () => void;
}

export function RefuelIntentModal({ merchantName, onConfirm, onClose }: RefuelIntentModalProps) {
  const [selectedIntent, setSelectedIntent] = useState<RefuelIntent | null>(null);
  const [partySize, setPartySize] = useState(1);
  const [needsPowerOutlet, setNeedsPowerOutlet] = useState(false);
  const [isToGo, setIsToGo] = useState(false);

  const handleContinue = () => {
    if (!selectedIntent) return;

    const details: RefuelDetails = {
      intent: selectedIntent,
      ...(selectedIntent === 'eat' && { partySize }),
      ...(selectedIntent === 'work' && { needsPowerOutlet }),
      ...(selectedIntent === 'quick-stop' && { isToGo }),
    };

    onConfirm(details);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl text-center mb-2">How are you refueling?</h2>
          <p className="text-sm text-[#65676B] text-center">
            This helps {merchantName} prepare for your arrival
          </p>
        </div>

        {/* Intent Options */}
        <div className="space-y-3 mb-6">
          {/* Eat Option */}
          <button
            onClick={() => setSelectedIntent('eat')}
            className={`w-full p-4 rounded-2xl border-2 transition-all text-left ${
              selectedIntent === 'eat'
                ? 'border-[#1877F2] bg-[#1877F2]/5'
                : 'border-[#E4E6EB] hover:border-[#1877F2]/30'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                selectedIntent === 'eat' ? 'bg-[#1877F2]' : 'bg-[#F7F8FA]'
              }`}>
                <Utensils className={`w-5 h-5 ${
                  selectedIntent === 'eat' ? 'text-white' : 'text-[#65676B]'
                }`} />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-base mb-1">Eat</h3>
                <p className="text-sm text-[#65676B]">Dine-in or grab a meal</p>
              </div>
            </div>
          </button>

          {/* Work Option */}
          <button
            onClick={() => setSelectedIntent('work')}
            className={`w-full p-4 rounded-2xl border-2 transition-all text-left ${
              selectedIntent === 'work'
                ? 'border-[#1877F2] bg-[#1877F2]/5'
                : 'border-[#E4E6EB] hover:border-[#1877F2]/30'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                selectedIntent === 'work' ? 'bg-[#1877F2]' : 'bg-[#F7F8FA]'
              }`}>
                <Laptop className={`w-5 h-5 ${
                  selectedIntent === 'work' ? 'text-white' : 'text-[#65676B]'
                }`} />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-base mb-1">Work</h3>
                <p className="text-sm text-[#65676B]">Need a workspace or WiFi</p>
              </div>
            </div>
          </button>

          {/* Quick Stop Option */}
          <button
            onClick={() => setSelectedIntent('quick-stop')}
            className={`w-full p-4 rounded-2xl border-2 transition-all text-left ${
              selectedIntent === 'quick-stop'
                ? 'border-[#1877F2] bg-[#1877F2]/5'
                : 'border-[#E4E6EB] hover:border-[#1877F2]/30'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                selectedIntent === 'quick-stop' ? 'bg-[#1877F2]' : 'bg-[#F7F8FA]'
              }`}>
                <Coffee className={`w-5 h-5 ${
                  selectedIntent === 'quick-stop' ? 'text-white' : 'text-[#65676B]'
                }`} />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-base mb-1">Quick Stop</h3>
                <p className="text-sm text-[#65676B]">Coffee, restroom, or to-go</p>
              </div>
            </div>
          </button>
        </div>

        {/* Sub-options based on intent */}
        {selectedIntent === 'eat' && (
          <div className="mb-6 bg-[#F7F8FA] rounded-2xl p-4">
            <label className="text-sm font-medium mb-3 block">Party Size</label>
            <div className="flex gap-2">
              {[1, 2, 3, 4].map((size) => (
                <button
                  key={size}
                  onClick={() => setPartySize(size)}
                  className={`flex-1 py-2 px-3 rounded-xl font-medium transition-all ${
                    partySize === size
                      ? 'bg-[#1877F2] text-white'
                      : 'bg-white text-[#050505] border border-[#E4E6EB]'
                  }`}
                >
                  {size}
                </button>
              ))}
              <button
                onClick={() => setPartySize(5)}
                className={`flex-1 py-2 px-3 rounded-xl font-medium transition-all ${
                  partySize === 5
                    ? 'bg-[#1877F2] text-white'
                    : 'bg-white text-[#050505] border border-[#E4E6EB]'
                }`}
              >
                5+
              </button>
            </div>
          </div>
        )}

        {selectedIntent === 'work' && (
          <div className="mb-6 bg-[#F7F8FA] rounded-2xl p-4">
            <button
              onClick={() => setNeedsPowerOutlet(!needsPowerOutlet)}
              className={`w-full py-3 rounded-xl font-medium transition-all ${
                needsPowerOutlet
                  ? 'bg-[#1877F2] text-white'
                  : 'bg-white text-[#050505] border border-[#E4E6EB]'
              }`}
            >
              {needsPowerOutlet ? '✓ ' : ''}Need Power Outlet
            </button>
          </div>
        )}

        {selectedIntent === 'quick-stop' && (
          <div className="mb-6 bg-[#F7F8FA] rounded-2xl p-4">
            <button
              onClick={() => setIsToGo(!isToGo)}
              className={`w-full py-3 rounded-xl font-medium transition-all ${
                isToGo
                  ? 'bg-[#1877F2] text-white'
                  : 'bg-white text-[#050505] border border-[#E4E6EB]'
              }`}
            >
              {isToGo ? '✓ ' : ''}To-Go Order
            </button>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-3">
          <button
            onClick={handleContinue}
            disabled={!selectedIntent}
            className={`w-full py-4 rounded-2xl font-medium transition-all ${
              selectedIntent
                ? 'bg-[#1877F2] text-white hover:bg-[#166FE5] active:scale-98'
                : 'bg-[#E4E6EB] text-[#65676B] cursor-not-allowed'
            }`}
          >
            Continue
          </button>
          <button
            onClick={onClose}
            className="w-full py-4 bg-white border-2 border-[#E4E6EB] text-[#050505] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-98 transition-all"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
