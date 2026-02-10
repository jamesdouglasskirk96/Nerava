import { useState } from 'react'
import { capture } from '../../analytics'
import { DRIVER_EVENTS } from '../../analytics/events'

const COLORS = ['White', 'Black', 'Blue', 'Red', 'Silver', 'Gray', 'Green', 'Other']
const POPULAR_EVS = [
  'Tesla Model 3', 'Tesla Model Y', 'Tesla Model S', 'Tesla Model X',
  'Rivian R1T', 'Rivian R1S', 'Ford Mustang Mach-E', 'Ford F-150 Lightning',
  'Chevrolet Bolt EV', 'Chevrolet Bolt EUV', 'Chevrolet Equinox EV',
  'Hyundai Ioniq 5', 'Hyundai Ioniq 6', 'Kia EV6', 'Kia EV9',
  'BMW iX', 'BMW i4', 'Mercedes EQS', 'Mercedes EQE',
  'Volkswagen ID.4', 'Polestar 2', 'Lucid Air', 'Nissan Ariya',
]

interface VehicleSetupProps {
  onSave: (color: string, model: string) => void
  onCancel: () => void
  isLoading?: boolean
}

export function VehicleSetup({ onSave, onCancel, isLoading }: VehicleSetupProps) {
  const [color, setColor] = useState('')
  const [model, setModel] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)

  const filteredEVs = model.length > 0
    ? POPULAR_EVS.filter(ev => ev.toLowerCase().includes(model.toLowerCase()))
    : []

  const handleSave = () => {
    if (!color || !model) return
    capture(DRIVER_EVENTS.EV_ARRIVAL_VEHICLE_SETUP, { color, model })
    onSave(color, model)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40">
      <div
        className="w-full max-w-md bg-white rounded-t-2xl p-6 pb-8 animate-slide-up"
        role="dialog"
        aria-label="Vehicle setup"
      >
        <div className="w-12 h-1 bg-gray-300 rounded-full mx-auto mb-6" />

        <h2 className="text-xl font-bold text-gray-900 mb-1">What do you drive?</h2>
        <p className="text-sm text-gray-500 mb-6">
          This helps merchants find you at the charger.
        </p>

        <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
        <select
          value={color}
          onChange={e => setColor(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-4 text-gray-900"
        >
          <option value="">Select color</option>
          {COLORS.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
        <div className="relative mb-6">
          <input
            type="text"
            value={model}
            onChange={e => {
              setModel(e.target.value)
              setShowSuggestions(true)
            }}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder="Tesla Model 3"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
          />
          {showSuggestions && filteredEVs.length > 0 && (
            <ul className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-40 overflow-y-auto">
              {filteredEVs.slice(0, 6).map(ev => (
                <li
                  key={ev}
                  className="px-3 py-2 hover:bg-gray-50 cursor-pointer text-sm"
                  onMouseDown={() => {
                    setModel(ev)
                    setShowSuggestions(false)
                  }}
                >
                  {ev}
                </li>
              ))}
            </ul>
          )}
        </div>

        <button
          onClick={handleSave}
          disabled={!color || !model || isLoading}
          className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Saving...' : 'Save'}
        </button>

        <button
          onClick={onCancel}
          className="w-full mt-3 text-gray-500 text-sm py-2"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
