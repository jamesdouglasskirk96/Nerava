interface SocialProofBadgeProps {
  neravaSessionsCount?: number;
  activeDriversCount?: number;
}

export function SocialProofBadge({ neravaSessionsCount, activeDriversCount }: SocialProofBadgeProps) {
  return (
    <div className="flex flex-col gap-1">
      {neravaSessionsCount && neravaSessionsCount > 0 && (
        <div className="flex items-center gap-1.5 text-xs text-[#65676B]">
          <span>🔥</span>
          <span>{neravaSessionsCount} Nerava sessions</span>
        </div>
      )}
      {activeDriversCount && activeDriversCount > 0 && (
        <div className="flex items-center gap-1.5 text-xs text-green-600">
          <span>⚡</span>
          <span>{activeDriversCount} EV driver{activeDriversCount > 1 ? 's' : ''} here now</span>
        </div>
      )}
    </div>
  );
}
