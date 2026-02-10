import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import type { ArrivalSession } from '../../services/arrival';
import {
  getStoredSessionToken,
  getSessionStatus,
  startSession,
} from '../../services/arrival';
import { CheckInPrompt } from './CheckInPrompt';
import { VerifyCarPrompt } from './VerifyCarPrompt';
import { GoToMerchantScreen } from './GoToMerchantScreen';
import { PromoCodeScreen } from './PromoCodeScreen';
import { ThankYouScreen } from './ThankYouScreen';
import { ErrorScreen } from './ErrorScreen';

export function MerchantArrivalScreen() {
  const { merchantId } = useParams<{ merchantId: string }>();
  const [session, setSession] = useState<ArrivalSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check for existing session on mount
  useEffect(() => {
    async function checkExistingSession() {
      const token = getStoredSessionToken();
      if (token) {
        try {
          const existingSession = await getSessionStatus(token);
          if (existingSession && existingSession.merchant?.id === merchantId) {
            setSession(existingSession);
          }
        } catch (e) {
          // Session expired or invalid, continue with new flow
          console.log('No valid existing session');
        }
      }
      setLoading(false);
    }
    checkExistingSession();
  }, [merchantId]);

  const handleCheckIn = async () => {
    if (!merchantId) return;

    try {
      setLoading(true);
      setError(null);
      const newSession = await startSession(merchantId);
      setSession(newSession);
    } catch (e) {
      setError('Failed to start check-in. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePinVerified = (updatedSession: ArrivalSession) => {
    setSession(updatedSession);
  };

  const handleArrived = (promoCode: string, expiresAt: string) => {
    setSession(prev => prev ? {
      ...prev,
      state: 'arrived',
      promo_code: promoCode,
      promo_code_expires_at: expiresAt,
    } : null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return <ErrorScreen message={error} onRetry={() => setError(null)} />;
  }

  if (!session) {
    return (
      <CheckInPrompt
        merchantId={merchantId!}
        onCheckIn={handleCheckIn}
      />
    );
  }

  switch (session.state) {
    case 'pending':
      return (
        <VerifyCarPrompt
          session={session}
          onVerified={handlePinVerified}
        />
      );

    case 'car_verified':
      return (
        <GoToMerchantScreen
          session={session}
          onArrived={handleArrived}
        />
      );

    case 'arrived':
      return (
        <PromoCodeScreen
          promoCode={session.promo_code!}
          expiresAt={session.promo_code_expires_at!}
          merchantName={session.merchant.name}
        />
      );

    case 'redeemed':
      return <ThankYouScreen merchantName={session.merchant.name} />;

    case 'expired':
    default:
      return (
        <ErrorScreen
          message="Your session has expired. Please start over."
          onRetry={() => {
            setSession(null);
          }}
        />
      );
  }
}
