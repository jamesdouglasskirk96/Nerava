import * as React from "react";

import { cn } from "./utils";

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex h-9 w-full border border-[#E4E6EB] bg-white px-3 py-2 text-sm text-[#050505] placeholder:text-[#65676B] focus:outline-none focus:border-[#1877F2] focus:ring-1 focus:ring-[#1877F2] disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
        className,
      )}
      {...props}
    />
  );
}

export { Input };