import { useEffect, useState } from 'react';

interface Props {
  promoCode: string;
  expiresAt: string;
  merchantName: string;
}

export function PromoCodeScreen({ promoCode, expiresAt, merchantName }: Props) {
  const [timeLeft, setTimeLeft] = useState<string>('');

  useEffect(() => {
    const updateTimer = () => {
      const now = new Date().getTime();
      const expires = new Date(expiresAt).getTime();
      const diff = expires - now;

      if (diff <= 0) {
        setTimeLeft('Expired');
        return;
      }

      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      setTimeLeft(`${minutes}:${seconds.toString().padStart(2, '0')}`);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [expiresAt]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-white">
      <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-2 mb-6">
        <div className="flex items-center space-x-2 text-green-700">
          <span className="text-xl">✓</span>
          <span className="font-semibold">You've arrived!</span>
        </div>
      </div>

      <h1 className="text-2xl font-bold text-gray-900 mb-8 text-center">
        Show this code to the cashier
      </h1>

      <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-8 mb-6 w-full max-w-md">
        <div className="text-6xl font-mono font-bold text-center text-gray-900 tracking-wider">
          {promoCode}
        </div>
      </div>

      <p className="text-gray-600 mb-2 text-center">
        Expires in <strong className="text-gray-900">{timeLeft}</strong>
      </p>

      <div className="mt-8 text-gray-500 text-center">
        <p>At {merchantName}</p>
      </div>
    </div>
  );
}
