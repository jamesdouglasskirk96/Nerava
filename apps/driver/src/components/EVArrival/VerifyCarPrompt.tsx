import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { ArrivalSession } from '../../services/arrival';
import { verifyPin, getStoredSessionToken } from '../../services/arrival';
import { Button } from '../shared/Button';
import { TeslaConnect } from '../TeslaConnect';

interface Props {
  session: ArrivalSession;
  onVerified: (session: ArrivalSession) => void;
  onBack?: () => void;
}

type VerifyMethod = 'choose' | 'pin' | 'tesla';

export function VerifyCarPrompt({ session: _session, onVerified, onBack }: Props) {
  const navigate = useNavigate();
  const [method, setMethod] = useState<VerifyMethod>('choose');
  const [pin, setPin] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate('/');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const token = getStoredSessionToken();
      if (!token) throw new Error('Session not found');

      const updatedSession = await verifyPin(token, pin);
      onVerified(updatedSession);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  const formatPin = (value: string): string => {
    // Auto-format as XXX-XXX
    const clean = value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
    if (clean.length > 3) {
      return `${clean.slice(0, 3)}-${clean.slice(3)}`;
    }
    return clean;
  };

  // Method selection screen
  if (method === 'choose') {
    return (
      <div className="flex flex-col min-h-screen p-6 bg-white">
        <button
          onClick={handleBack}
          className="flex items-center text-gray-600 mb-6"
        >
          <svg className="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>

        <div className="flex-1 flex flex-col items-center justify-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4 text-center">
          Verify Your EV
        </h1>
        <p className="text-gray-600 text-center mb-8 max-w-md">
          Choose how you'd like to verify your charging session
        </p>

        <div className="w-full max-w-md space-y-4">
          {/* Tesla Connect Option - Recommended */}
          <button
            onClick={() => setMethod('tesla')}
            className="w-full p-4 bg-white border-2 border-red-500 rounded-xl text-left hover:bg-red-50 transition-colors"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-red-600" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2L2 7v10l10 5 10-5V7L12 2z"/>
                </svg>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900">Connect Tesla</span>
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                    Recommended
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Link your Tesla account for automatic verification
                </p>
              </div>
            </div>
          </button>

          {/* Car Browser Option */}
          <button
            onClick={() => setMethod('pin')}
            className="w-full p-4 bg-white border border-gray-200 rounded-xl text-left hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-2xl">🚗</span>
              </div>
              <div>
                <span className="font-semibold text-gray-900">Car Browser Code</span>
                <p className="text-sm text-gray-600 mt-1">
                  Enter a code from your car's browser
                </p>
              </div>
            </div>
          </button>
        </div>
        </div>
      </div>
    );
  }

  // Tesla Connect screen
  if (method === 'tesla') {
    return (
      <div className="flex flex-col min-h-screen p-6 bg-gray-50">
        <button
          onClick={() => setMethod('choose')}
          className="flex items-center text-gray-600 mb-6"
        >
          <svg className="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>

        <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Connect Your Tesla
        </h1>

        <TeslaConnect
          onCodeGenerated={(code) => {
            console.log('EV Code generated:', code);
            // Optionally update session or navigate
          }}
        />
      </div>
    );
  }

  // PIN entry screen
  return (
    <div className="flex flex-col min-h-screen p-6 bg-white">
      <button
        onClick={() => setMethod('choose')}
        className="flex items-center text-gray-600 mb-6"
      >
        <svg className="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back
      </button>

      <div className="flex-1 flex flex-col items-center justify-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
          Enter Car Code
        </h1>

        <div className="space-y-4 mb-8 w-full max-w-md">
          <div className="flex items-start space-x-3">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold">
              1
            </span>
            <span className="text-gray-700 pt-1">
              Open <strong className="font-semibold">link.nerava.network</strong> in your car browser
            </span>
          </div>
          <div className="flex items-start space-x-3">
            <span className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold">
              2
            </span>
            <span className="text-gray-700 pt-1">
              Enter the code shown on your car screen below
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="w-full max-w-md">
          <input
            type="text"
            value={pin}
            onChange={(e) => setPin(formatPin(e.target.value))}
            placeholder="XXX-XXX"
            className="w-full px-4 py-3 text-2xl font-mono text-center border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 mb-4 uppercase tracking-wider"
            maxLength={7}
            autoComplete="off"
            autoFocus
          />

          {error && (
            <div className="text-red-600 text-sm mb-4 text-center">{error}</div>
          )}

          <Button
            type="submit"
            disabled={pin.length < 7 || loading}
            className="w-full"
          >
            {loading ? 'Verifying...' : 'Verify'}
          </Button>
        </form>
      </div>
    </div>
  );
}
