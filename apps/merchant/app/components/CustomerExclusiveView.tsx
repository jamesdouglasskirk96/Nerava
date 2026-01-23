import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { CheckCircle, Clock } from 'lucide-react';

// Mock exclusive data
const mockExclusiveData = {
  '1': {
    merchantName: 'Downtown Coffee Shop',
    exclusiveName: 'Free Pastry with Coffee',
    staffInstructions: 'Provide any pastry from display case with coffee purchase',
    activatedAt: new Date(),
  },
};

export function CustomerExclusiveView() {
  const { exclusiveId } = useParams();
  const [timeRemaining, setTimeRemaining] = useState(300); // 5 minutes in seconds
  
  // Countdown timer
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeRemaining(prev => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const exclusive = mockExclusiveData[exclusiveId as keyof typeof mockExclusiveData];

  if (!exclusive) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
        <div className="text-center">
          <h1 className="text-2xl text-neutral-900">Exclusive Not Found</h1>
        </div>
      </div>
    );
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-6">
      <div className="max-w-lg w-full">
        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          {/* Merchant Info */}
          <div className="text-center mb-8">
            <div className="text-sm text-neutral-600 mb-2">Exclusive at</div>
            <h1 className="text-2xl text-neutral-900">{exclusive.merchantName}</h1>
          </div>

          {/* Active Badge */}
          <div className="bg-green-100 rounded-2xl p-8 mb-8">
            <div className="flex flex-col items-center text-center">
              <div className="mb-4">
                <div className="p-4 bg-white rounded-full shadow-sm">
                  <CheckCircle className="w-12 h-12 text-green-600" />
                </div>
              </div>
              <h2 className="text-xl text-green-900 mb-2">Exclusive Active</h2>
              <p className="text-lg text-green-800">{exclusive.exclusiveName}</p>
            </div>
          </div>

          {/* Countdown */}
          <div className="bg-neutral-50 rounded-xl p-6 mb-8">
            <div className="flex items-center justify-center gap-3">
              <Clock className="w-6 h-6 text-neutral-600" />
              <div>
                <div className="text-xs text-neutral-600 mb-1">Time Remaining</div>
                <div className="text-3xl text-neutral-900 tabular-nums">{formatTime(timeRemaining)}</div>
              </div>
            </div>
          </div>

          {/* Staff Instructions */}
          {exclusive.staffInstructions && (
            <div className="border-t border-neutral-200 pt-6">
              <div className="text-xs text-neutral-600 mb-2">Staff Instructions</div>
              <p className="text-sm text-neutral-900">{exclusive.staffInstructions}</p>
            </div>
          )}
        </div>

        {/* Info Footer */}
        <div className="text-center">
          <p className="text-sm text-neutral-600">
            Show this screen to staff to redeem your exclusive
          </p>
        </div>
      </div>
    </div>
  );
}
