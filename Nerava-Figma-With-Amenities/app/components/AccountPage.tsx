import { ArrowLeft, Heart, Settings, QrCode, LogOut, ChevronRight } from "lucide-react";
import { useState } from "react";

interface AccountPageProps {
  onClose: () => void;
  likedMerchantsCount: number;
  onLogout: () => void;
  onViewFavorites: () => void;
}

export function AccountPage({ onClose, likedMerchantsCount, onLogout, onViewFavorites }: AccountPageProps) {
  const [showReferralCode, setShowReferralCode] = useState(false);

  // Generate a unique referral code (in production, this would come from backend)
  const referralCode = "NERAVA-EV-2025";

  return (
    <>
      <div className="fixed inset-0 bg-white z-50">
        <div className="h-screen max-w-md mx-auto bg-white flex flex-col">
          {/* Header */}
          <div className="bg-white border-b border-[#E4E6EB] px-5 py-4 flex-shrink-0">
            <div className="flex items-center justify-between">
              <button
                onClick={onClose}
                className="w-10 h-10 bg-[#F7F8FA] rounded-full flex items-center justify-center hover:bg-[#E4E6EB] active:scale-95 transition-all"
              >
                <ArrowLeft className="w-5 h-5 text-[#050505]" />
              </button>
              <h1 className="text-lg font-semibold">Account</h1>
              <div className="w-10" /> {/* Spacer for centering */}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-5 py-4">
            {/* Favorites */}
            <button
              onClick={onViewFavorites}
              className="w-full bg-white border border-[#E4E6EB] rounded-2xl p-4 mb-3 hover:bg-[#F7F8FA] active:scale-[0.98] transition-all flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-red-50 rounded-full flex items-center justify-center">
                  <Heart className="w-5 h-5 text-red-500" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-[#050505]">Favorites</p>
                  <p className="text-sm text-[#65676B]">{likedMerchantsCount} saved</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-[#65676B]" />
            </button>

            {/* Share Nerava - Referral QR Code */}
            <button
              onClick={() => setShowReferralCode(true)}
              className="w-full bg-gradient-to-r from-[#1877F2]/5 to-[#1877F2]/10 border-2 border-[#1877F2]/30 rounded-2xl p-4 mb-3 hover:from-[#1877F2]/10 hover:to-[#1877F2]/15 active:scale-[0.98] transition-all flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#1877F2]/10 rounded-full flex items-center justify-center">
                  <QrCode className="w-5 h-5 text-[#1877F2]" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-[#1877F2]">Share Nerava</p>
                  <p className="text-sm text-[#1877F2]/70">Earn rewards for referrals</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-[#1877F2]" />
            </button>

            {/* Settings */}
            <button
              onClick={() => alert("Settings coming soon")}
              className="w-full bg-white border border-[#E4E6EB] rounded-2xl p-4 mb-3 hover:bg-[#F7F8FA] active:scale-[0.98] transition-all flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#F7F8FA] rounded-full flex items-center justify-center">
                  <Settings className="w-5 h-5 text-[#050505]" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-[#050505]">Settings</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-[#65676B]" />
            </button>

            {/* Log Out */}
            <button
              onClick={onLogout}
              className="w-full bg-red-50 border border-red-200 rounded-2xl p-4 hover:bg-red-100 active:scale-[0.98] transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
                  <LogOut className="w-5 h-5 text-red-600" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-red-600">Log out</p>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Referral QR Code Modal */}
      {showReferralCode && (
        <div className="fixed inset-0 bg-white z-[60] overflow-y-auto">
          <div className="min-h-screen max-w-md mx-auto p-6 pb-8">
            <button
              onClick={() => setShowReferralCode(false)}
              className="absolute top-6 left-6 w-12 h-12 bg-[#F7F8FA] rounded-full flex items-center justify-center hover:bg-[#E4E6EB] active:scale-95 transition-all"
            >
              <ArrowLeft className="w-6 h-6 text-[#050505]" />
            </button>

            <div className="text-center pt-8">
              {/* Header */}
              <div className="mb-6">
                <div className="w-16 h-16 bg-[#1877F2]/10 rounded-full flex items-center justify-center mx-auto mb-3">
                  <QrCode className="w-8 h-8 text-[#1877F2]" />
                </div>
                <h1 className="text-2xl font-bold mb-2">Share Nerava</h1>
                <p className="text-sm text-[#65676B]">
                  Share with EV drivers or merchants
                </p>
              </div>

              {/* QR Code Container */}
              <div className="bg-white rounded-3xl p-5 mb-4 border-2 border-[#E4E6EB] shadow-lg">
                {/* Placeholder QR Code - In production, use a QR code library */}
                <div className="w-56 h-56 mx-auto bg-[#F7F8FA] rounded-2xl flex items-center justify-center mb-4">
                  <div className="text-center">
                    <QrCode className="w-20 h-20 text-[#1877F2] mx-auto mb-2" />
                    <p className="text-sm text-[#65676B]">QR Code</p>
                  </div>
                </div>

                {/* Referral Code */}
                <div className="bg-[#1877F2]/5 rounded-xl p-3 border border-[#1877F2]/20">
                  <p className="text-xs text-[#65676B] mb-1 text-center">Referral Code</p>
                  <p className="text-lg font-mono font-bold text-[#1877F2] text-center tracking-wider">
                    {referralCode}
                  </p>
                </div>
              </div>

              {/* Benefits */}
              <div className="bg-gradient-to-r from-[#1877F2]/5 to-[#1877F2]/10 rounded-2xl p-4 mb-4 border border-[#1877F2]/20">
                <p className="text-sm text-[#1877F2] font-medium mb-2">🎁 Referral Rewards</p>
                <div className="space-y-1 text-left text-xs text-[#050505]">
                  <p>• Driver referral: Both get $5 credit</p>
                  <p>• Merchant referral: Free month premium</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3">
                <button
                  onClick={async () => {
                    const referralLink = `Join Nerava with my code: ${referralCode}\nhttps://nerava.com/join/${referralCode}`;
                    try {
                      await navigator.clipboard.writeText(referralLink);
                      alert('Referral link copied to clipboard!');
                    } catch (error) {
                      // Fallback: Show the link in an alert for manual copying
                      const message = `Copy this referral link:\n\n${referralLink}`;
                      prompt('Copy this referral link:', referralLink);
                    }
                  }}
                  className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-98 transition-all"
                >
                  Copy Referral Link
                </button>
                
                <button
                  onClick={() => {
                    if (navigator.share) {
                      navigator.share({
                        title: 'Join Nerava',
                        text: `Join Nerava - the Moment of Charge Discovery Network. Use my code: ${referralCode}`,
                        url: `https://nerava.com/join/${referralCode}`
                      }).catch(() => {
                        // User cancelled share or error occurred
                      });
                    } else {
                      // Fallback: Show the link for manual sharing
                      const referralLink = `Join Nerava with my code: ${referralCode}\nhttps://nerava.com/join/${referralCode}`;
                      prompt('Copy this referral link to share:', referralLink);
                    }
                  }}
                  className="w-full py-4 bg-white border-2 border-[#1877F2] text-[#1877F2] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-98 transition-all"
                >
                  Share Link
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}