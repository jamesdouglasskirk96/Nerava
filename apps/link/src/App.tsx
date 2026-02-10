import { useEffect, useState } from 'react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_URL || '';

interface PinResponse {
  pin: string;
  expires_in_seconds: number;
  display_message: string;
}

export default function App() {
  const [pin, setPin] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expiresIn, setExpiresIn] = useState<number>(300);
  const [loading, setLoading] = useState(true);

  const generatePin = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/v1/arrival/car-pin`, {
        method: 'POST',
      });

      if (response.status === 403) {
        setError('This page only works in your car browser');
        setLoading(false);
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to generate code');
      }

      const data: PinResponse = await response.json();
      setPin(data.pin);
      setExpiresIn(data.expires_in_seconds);
    } catch (e) {
      setError('Failed to generate code. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  // Generate PIN on mount
  useEffect(() => {
    generatePin();
  }, []);

  // Countdown timer
  useEffect(() => {
    if (!pin || expiresIn <= 0) return;

    const timer = setInterval(() => {
      setExpiresIn((prev) => {
        if (prev <= 1) {
          // Auto-refresh when expired
          generatePin();
          return 300;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [pin]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading && !pin) {
    return (
      <div className="container">
        <img src="/nerava-logo.png" alt="Nerava" className="logo" />
        <div className="loading">Generating code...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container error-container">
        <img src="/nerava-logo.png" alt="Nerava" className="logo" />
        <h1>EV Browser Required</h1>
        <p className="error-message">{error}</p>
        <p className="help-text">
          Open this page in your Tesla or EV car browser to get your check-in code.
        </p>
      </div>
    );
  }

  return (
    <div className="container">
      <img src="/nerava-logo.png" alt="Nerava" className="logo" />

      <h1>Enter this code on your phone</h1>

      <div className="pin-display">{pin}</div>

      <p className="expires">
        Expires in {formatTime(expiresIn)}
      </p>

      <button onClick={generatePin} className="refresh-button" disabled={loading}>
        {loading ? 'Generating...' : 'Get New Code'}
      </button>
    </div>
  );
}
