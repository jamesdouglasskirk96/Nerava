import { capture } from '../../analytics'
import { DRIVER_EVENTS } from '../../analytics/events'

export type ArrivalMode = 'ev_curbside' | 'ev_dine_in'

interface ModeSelectorProps {
  mode: ArrivalMode
  onChange: (mode: ArrivalMode) => void
}

export function ModeSelector({ mode, onChange }: ModeSelectorProps) {
  const handleChange = (newMode: ArrivalMode) => {
    if (newMode !== mode) {
      onChange(newMode)
      capture(DRIVER_EVENTS.EV_ARRIVAL_MODE_CHANGED, { mode: newMode })
    }
  }

  return (
    <div className="flex bg-gray-100 rounded-lg p-1 mb-4" role="tablist">
      <button
        role="tab"
        aria-selected={mode === 'ev_curbside'}
        className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
          mode === 'ev_curbside'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-500 hover:text-gray-700'
        }`}
        onClick={() => handleChange('ev_curbside')}
      >
        EV Curbside
      </button>
      <button
        role="tab"
        aria-selected={mode === 'ev_dine_in'}
        className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
          mode === 'ev_dine_in'
            ? 'bg-white text-blue-600 shadow-sm'
            : 'text-gray-500 hover:text-gray-700'
        }`}
        onClick={() => handleChange('ev_dine_in')}
      >
        EV Dine-In
      </button>
    </div>
  )
}
