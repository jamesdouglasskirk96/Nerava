import { Car } from "lucide-react";

interface SocialProofBadgeProps {
  neravaSessionsCount?: number;
  activeDriversCount?: number;
}

export function SocialProofBadge({ neravaSessionsCount, activeDriversCount }: SocialProofBadgeProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {neravaSessionsCount && neravaSessionsCount > 0 && (
        <div className="flex items-center gap-1.5 text-sm text-[#050505]">
          <Car className="w-4 h-4 text-[#1877F2]" />
          <span className="font-medium">{neravaSessionsCount} drivers visited</span>
        </div>
      )}
      {activeDriversCount && activeDriversCount > 0 && (
        <div className="flex items-center gap-1.5 text-xs text-green-600">
          <div className="w-1.5 h-1.5 bg-green-600 rounded-full animate-pulse" />
          <span className="font-medium">{activeDriversCount} here now</span>
        </div>
      )}
    </div>
  );
}