// Demo mode toggle component for header
import { useDemoMode } from '../../hooks/useDemoMode'

export function DemoModeToggle() {
  const { isDemoMode, currentState, toggleState } = useDemoMode()

  if (!isDemoMode) return null

  return (
    <button
      onClick={toggleState}
      className="px-3 py-1.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors flex items-center gap-2"
      aria-label="Toggle demo mode"
    >
      <span>{currentState === 'charging' ? 'Charging' : 'Pre-Charging'}</span>
      <svg
        className="w-3 h-3"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
        />
      </svg>
    </button>
  )
}

