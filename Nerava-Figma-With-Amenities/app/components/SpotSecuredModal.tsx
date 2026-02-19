import { Wallet } from "lucide-react";
import type { RefuelDetails } from "./RefuelIntentModal";

interface SpotSecuredModalProps {
  merchantName: string;
  merchantBadge?: string;
  refuelDetails: RefuelDetails;
  remainingMinutes: number;
  verificationCode: string;
  onViewWallet: () => void;
}

export function SpotSecuredModal({
  merchantName,
  merchantBadge,
  refuelDetails,
  remainingMinutes,
  verificationCode,
  onViewWallet,
}: SpotSecuredModalProps) {
  const getIntentLabel = () => {
    switch (refuelDetails.intent) {
      case 'eat':
        return `DINING: PARTY OF ${refuelDetails.partySize}`;
      case 'work':
        return `WORK SESSION${refuelDetails.needsPowerOutlet ? ' + POWER' : ''}`;
      case 'quick-stop':
        return `QUICK STOP${refuelDetails.isToGo ? ' (TO-GO)' : ''}`;
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50 p-4">
      <div className="bg-white rounded-3xl p-8 max-w-md w-full mb-8 shadow-2xl">
        {/* Icon */}
        <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <Wallet className="w-8 h-8 text-[#1877F2]" />
        </div>

        {/* Title */}
        <h2 className="text-2xl text-center mb-3">Spot Secured</h2>

        {/* Time remaining */}
        <div className="flex justify-center mb-4">
          <div className="bg-[#1877F2]/10 rounded-full px-4 py-2">
            <p className="text-sm text-[#1877F2] font-medium">
              Spot held for {remainingMinutes} {remainingMinutes === 1 ? 'minute' : 'minutes'}
            </p>
          </div>
        </div>

        {/* Description */}
        <p className="text-center text-[#65676B] mb-6">
          Your spot is secured while you're charging.<br />
          Show this at {merchantName}.
        </p>

        {/* Reservation Card with PROMINENT intent */}
        <div className="bg-[#F7F8FA] rounded-2xl p-5 mb-6 border border-[#E4E6EB]">
          {/* Large Intent Text */}
          <div className="mb-4 text-center">
            <p className="text-2xl font-bold text-[#1877F2] tracking-wide">
              {getIntentLabel()}
            </p>
          </div>

          {/* Merchant info */}
          <div className="flex items-center justify-between mb-3 pb-3 border-b border-[#E4E6EB]">
            <h3 className="font-medium text-base">{merchantName}</h3>
            {merchantBadge && (
              <div className="px-2.5 py-1 bg-yellow-500/10 rounded-full border border-yellow-500/20">
                <span className="text-xs text-yellow-700">{merchantBadge}</span>
              </div>
            )}
          </div>

          {/* Verification Code */}
          <div className="bg-white rounded-xl p-3 border border-[#E4E6EB]">
            <p className="text-xs text-[#65676B] mb-1 text-center">Reservation ID</p>
            <p className="text-lg font-mono font-medium text-center tracking-wider">
              {verificationCode}
            </p>
          </div>
        </div>

        {/* View Reservation Button */}
        <button
          onClick={onViewWallet}
          className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
        >
          View Reservation
        </button>
      </div>
    </div>
  );
}