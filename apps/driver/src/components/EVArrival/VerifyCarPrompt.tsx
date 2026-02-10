import { useState } from 'react';
import type { ArrivalSession } from '../../services/arrival';
import { verifyPin, getStoredSessionToken } from '../../services/arrival';
import { Button } from '../shared/Button';

interface Props {
  session: ArrivalSession;
  onVerified: (session: ArrivalSession) => void;
}

export function VerifyCarPrompt({ session: _session, onVerified }: Props) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-white">
      <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
        Verify Your EV
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
  );
}
