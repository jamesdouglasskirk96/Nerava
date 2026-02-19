import { useState } from 'react';
import { api } from '../../services/api';
import { capture, DRIVER_EVENTS } from '../../analytics';

const COLORS = [
  { value: 'white', label: 'White', emoji: '⬜' },
  { value: 'black', label: 'Black', emoji: '⬛' },
  { value: 'blue', label: 'Blue', emoji: '🟦' },
  { value: 'red', label: 'Red', emoji: '🟥' },
  { value: 'silver', label: 'Silver', emoji: '🔘' },
  { value: 'gray', label: 'Gray', emoji: '🩶' },
  { value: 'other', label: 'Other', emoji: '🎨' },
];

interface VehicleSetupPromptProps {
  onComplete: () => void;
}

export function VehicleSetupPrompt({ onComplete }: VehicleSetupPromptProps) {
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!selectedColor) return;

    setLoading(true);
    capture(DRIVER_EVENTS.VEHICLE_COLOR_SET, { color: selectedColor });

    try {
      await api.put('/v1/account/vehicle', {
        color: selectedColor,
        model: 'Tesla', // We know it's a Tesla from browser
      });
      onComplete();
    } catch (error) {
      console.error('Failed to save vehicle:', error);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col justify-center p-6">
      <div className="max-w-md mx-auto text-center">
        <div className="text-5xl mb-4">🚗</div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          One quick thing...
        </h1>

        <p className="text-gray-600 mb-8">
          What color is your Tesla?
          <br />
          <span className="text-sm">
            This helps restaurants find you at the charger.
          </span>
        </p>

        <div className="grid grid-cols-4 gap-3 mb-8">
          {COLORS.map((color) => (
            <button
              key={color.value}
              onClick={() => setSelectedColor(color.value)}
              className={`p-3 rounded-lg border-2 transition-all ${
                selectedColor === color.value
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-1">{color.emoji}</div>
              <div className="text-xs text-gray-600">{color.label}</div>
            </button>
          ))}
        </div>

        <button
          onClick={handleSave}
          disabled={!selectedColor || loading}
          className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg
                     font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Saving...' : 'Continue'}
        </button>
      </div>
    </div>
  );
}
