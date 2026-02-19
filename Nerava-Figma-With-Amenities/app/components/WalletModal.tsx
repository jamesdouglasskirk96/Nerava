import { X, Car } from "lucide-react";

interface Merchant {
  id: string;
  name: string;
  category?: string;
  exclusiveOffer?: string;
}

interface WalletModalProps {
  activeExclusives: Merchant[];
  expiredExclusives: Merchant[];
  onClose: () => void;
  onExclusiveClick: (merchant: Merchant) => void;
  onViewActiveExclusive?: () => void;
}

export function WalletModal({
  activeExclusives,
  expiredExclusives,
  onClose,
  onExclusiveClick,
  onViewActiveExclusive,
}: WalletModalProps) {
  const hasContent = activeExclusives.length > 0 || expiredExclusives.length > 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-[70] p-4">
      <div className="bg-white rounded-3xl max-w-md w-full mb-8 shadow-2xl max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#E4E6EB] flex-shrink-0">
          <div className="flex items-center gap-2">
            <Car className="w-5 h-5 text-[#1877F2]" />
            <h2 className="text-xl font-medium">My Sessions</h2>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 bg-[#F7F8FA] rounded-full flex items-center justify-center hover:bg-[#E4E6EB] active:scale-95 transition-all"
          >
            <X className="w-5 h-5 text-[#050505]" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {!hasContent && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-[#F7F8FA] rounded-full flex items-center justify-center mx-auto mb-4">
                <Car className="w-8 h-8 text-[#65676B]" />
              </div>
              <p className="text-[#65676B]">No active sessions</p>
              <p className="text-sm text-[#65676B] mt-1">
                Secure a spot to see it here
              </p>
            </div>
          )}

          {/* Active Sessions */}
          {activeExclusives.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-[#65676B] mb-3">Active Sessions</h3>
              <div className="space-y-3">
                {activeExclusives.map((merchant) => (
                  <button
                    key={merchant.id}
                    onClick={() => {
                      if (onViewActiveExclusive) {
                        onViewActiveExclusive();
                      }
                    }}
                    className="w-full bg-[#1877F2]/5 border border-[#1877F2]/20 rounded-2xl p-4 text-left hover:bg-[#1877F2]/10 active:scale-98 transition-all"
                  >
                    <h4 className="font-medium mb-1">{merchant.name}</h4>
                    {merchant.category && (
                      <p className="text-xs text-[#65676B] mb-2">{merchant.category}</p>
                    )}
                    {merchant.exclusiveOffer && (
                      <p className="text-xs text-[#1877F2]">{merchant.exclusiveOffer}</p>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Past Visits */}
          {expiredExclusives.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-[#65676B] mb-3">Past Visits</h3>
              <div className="space-y-3">
                {expiredExclusives.map((merchant) => (
                  <div
                    key={merchant.id}
                    className="w-full bg-[#F7F8FA] border border-[#E4E6EB] rounded-2xl p-4"
                  >
                    <h4 className="font-medium mb-1 text-[#65676B]">{merchant.name}</h4>
                    {merchant.category && (
                      <p className="text-xs text-[#65676B]">{merchant.category}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}