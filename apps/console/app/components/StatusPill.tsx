interface StatusPillProps {
  status: string;
}

const statusStyles: Record<string, string> = {
  active: "bg-green-100 text-green-700 border-green-200",
  paused: "bg-yellow-100 text-yellow-700 border-yellow-200",
  exhausted: "bg-red-100 text-red-700 border-red-200",
  draft: "bg-gray-100 text-gray-700 border-gray-200",
  completed: "bg-blue-100 text-blue-700 border-blue-200",
  canceled: "bg-red-100 text-red-700 border-red-200",
};

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function StatusPill({ status }: StatusPillProps) {
  const key = status.toLowerCase();
  const style = statusStyles[key] || "bg-gray-100 text-gray-700 border-gray-200";
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium border ${style}`}
    >
      {capitalize(key)}
    </span>
  );
}
