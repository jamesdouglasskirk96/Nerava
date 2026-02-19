interface LiveStallIndicatorProps {
  availableStalls: number;
  totalStalls: number;
}

export function LiveStallIndicator({ availableStalls, totalStalls }: LiveStallIndicatorProps) {
  return (
    <div className="flex items-center gap-2">
      {/* Visual dots */}
      <div className="flex gap-0.5">
        {Array.from({ length: Math.min(totalStalls, 5) }).map((_, index) => (
          <div
            key={index}
            className={`w-2 h-2 rounded-full ${
              index < availableStalls 
                ? "bg-green-500" 
                : "bg-gray-300"
            }`}
          />
        ))}
      </div>
      {/* Text label */}
      <span className="text-xs text-[#65676B]">
        {availableStalls > 0 ? (
          <span className="text-green-600 font-medium">{availableStalls} open now</span>
        ) : (
          <span className="text-red-600 font-medium">Full</span>
        )}
      </span>
    </div>
  );
}
