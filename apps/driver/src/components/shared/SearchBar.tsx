import { Search, X } from 'lucide-react'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
}

export function SearchBar({ value, onChange }: SearchBarProps) {
  return (
    <div className="px-4 pb-2 flex-shrink-0">
      <form
        className="relative flex items-center"
        onSubmit={(e) => e.preventDefault()}
      >
        <Search className="absolute left-3.5 w-4.5 h-4.5 text-[#65676B] pointer-events-none" aria-hidden="true" />
        <input
          type="search"
          inputMode="search"
          enterKeyHint="search"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }}
          placeholder="What to do while you charge"
          className="w-full pl-10 pr-9 py-2.5 bg-[#F7F8FA] rounded-full text-[16px] text-[#050505] placeholder-[#65676B] border border-[#E4E6EB] focus:outline-none focus:border-[#1877F2] focus:ring-1 focus:ring-[#1877F2] transition-colors"
          aria-label="Search merchants"
        />
        {value && (
          <button
            type="button"
            onClick={() => onChange('')}
            className="absolute right-3 p-0.5 rounded-full hover:bg-[#E4E6EB] transition-colors"
            aria-label="Clear search"
          >
            <X className="w-4 h-4 text-[#65676B]" />
          </button>
        )}
      </form>
    </div>
  )
}
