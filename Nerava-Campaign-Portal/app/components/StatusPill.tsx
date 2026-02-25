interface StatusPillProps {
  status: "Active" | "Paused" | "Exhausted" | "Draft" | "Completed";
}

const statusStyles = {
  Active: "bg-green-100 text-green-700 border-green-200",
  Paused: "bg-yellow-100 text-yellow-700 border-yellow-200",
  Exhausted: "bg-red-100 text-red-700 border-red-200",
  Draft: "bg-gray-100 text-gray-700 border-gray-200",
  Completed: "bg-blue-100 text-blue-700 border-blue-200",
};

export function StatusPill({ status }: StatusPillProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium ${statusStyles[status]}`}
    >
      {status}
    </span>
  );
}