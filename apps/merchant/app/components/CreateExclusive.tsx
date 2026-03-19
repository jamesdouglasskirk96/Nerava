import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Info, CreditCard, Zap, ChevronRight, Check, Loader2 } from 'lucide-react';
import { createExclusive, getPaymentStatus, setupCard, ApiError, type PaymentStatus } from '../services/api';
import { capture, MERCHANT_EVENTS } from '../analytics';

type Step = 'billing' | 'details';

export function CreateExclusive() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('billing');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | null>(null);
  const [paymentLoading, setPaymentLoading] = useState(true);
  const merchantId = localStorage.getItem('merchant_id') || '';

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    dailyCap: '100',
  });

  useEffect(() => {
    capture(MERCHANT_EVENTS.EXCLUSIVE_CREATE_OPEN);
    loadPaymentStatus();
  }, []);

  // Check for card_saved return from Stripe
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('card_saved') === 'true') {
      // Reload payment status after card setup
      loadPaymentStatus();
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  const loadPaymentStatus = () => {
    setPaymentLoading(true);
    getPaymentStatus()
      .then((status) => {
        setPaymentStatus(status);
        // If already has billing set up, skip to details
        if (status.billing_type === 'pay_as_you_go' || status.billing_type === 'campaign') {
          setStep('details');
        }
      })
      .catch(() => setPaymentStatus(null))
      .finally(() => setPaymentLoading(false));
  };

  const handleAddCard = async () => {
    setLoading(true);
    try {
      const { checkout_url } = await setupCard();
      window.location.href = checkout_url;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to start card setup');
      setLoading(false);
    }
  };

  const handleSelectPayAsYouGo = () => {
    if (paymentStatus?.has_card) {
      setStep('details');
    } else {
      handleAddCard();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!merchantId) {
      setError('No merchant ID found. Please complete the claim flow.');
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const result = await createExclusive(merchantId, {
        title: formData.name,
        description: formData.description,
        daily_cap: parseInt(formData.dailyCap) || undefined,
        eligibility: 'charging_only',
      });

      capture(MERCHANT_EVENTS.EXCLUSIVE_CREATE_SUBMIT_SUCCESS, {
        exclusive_id: result.id,
        merchant_id: merchantId,
      });

      navigate('/exclusives');
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to create exclusive';
      capture(MERCHANT_EVENTS.EXCLUSIVE_CREATE_SUBMIT_FAIL, {
        error: errorMessage,
        merchant_id: merchantId,
      });
      setError(errorMessage);
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (paymentLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-neutral-400" />
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={() => step === 'details' && paymentStatus?.billing_type === 'free' ? setStep('billing') : navigate('/exclusives')}
        className="flex items-center gap-2 text-neutral-600 hover:text-neutral-900 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        {step === 'details' && paymentStatus?.billing_type === 'free' ? 'Back to Billing' : 'Back to Exclusives'}
      </button>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {step === 'billing' && (
        <div>
          <div className="mb-8">
            <h1 className="text-3xl text-neutral-900 mb-2">Choose a Billing Plan</h1>
            <p className="text-neutral-600">
              Select how you want to pay for exclusive claims from EV drivers.
            </p>
          </div>

          <div className="max-w-3xl grid gap-4">
            {/* Pay As You Go */}
            <button
              onClick={handleSelectPayAsYouGo}
              disabled={loading}
              className="bg-white p-6 rounded-lg border-2 border-neutral-200 hover:border-neutral-900 transition-colors text-left group disabled:opacity-50"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="p-2.5 bg-green-50 rounded-lg">
                    <CreditCard className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-neutral-900 mb-1">Pay As You Go</h3>
                    <p className="text-sm text-neutral-600 mb-3">
                      Card on file. Only charged when a driver claims your offer.
                    </p>
                    <div className="text-2xl font-bold text-neutral-900">
                      $1.50 <span className="text-sm font-normal text-neutral-500">per claim</span>
                    </div>
                    <p className="text-xs text-neutral-500 mt-1">
                      No minimum. No commitment. Pause anytime.
                    </p>
                    {paymentStatus?.has_card && (
                      <div className="mt-3 flex items-center gap-2 text-sm text-green-700">
                        <Check className="w-4 h-4" />
                        <span>{paymentStatus.card_brand} ****{paymentStatus.card_last4} on file</span>
                      </div>
                    )}
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-neutral-400 group-hover:text-neutral-900 mt-1" />
              </div>
            </button>

            {/* Campaign (Prepaid) */}
            <button
              onClick={() => setStep('details')}
              className="bg-white p-6 rounded-lg border-2 border-neutral-200 hover:border-neutral-900 transition-colors text-left group"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="p-2.5 bg-blue-50 rounded-lg">
                    <Zap className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-neutral-900 mb-1">Campaign Credits</h3>
                    <p className="text-sm text-neutral-600 mb-3">
                      Prepay for a fixed budget. Better per-claim rate at higher volumes.
                    </p>
                    <div className="text-2xl font-bold text-neutral-900">
                      $1.00 <span className="text-sm font-normal text-neutral-500">per claim</span>
                    </div>
                    <p className="text-xs text-neutral-500 mt-1">
                      $50 minimum deposit. Auto-pauses when budget runs out.
                    </p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-neutral-400 group-hover:text-neutral-900 mt-1" />
              </div>
            </button>
          </div>

          <div className="max-w-3xl mt-6 bg-neutral-50 p-4 rounded-lg">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-neutral-500 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-neutral-600">
                <strong>What counts as a claim?</strong> A driver must be actively charging their EV within walking distance of your business and tap "Claim Offer" in the Nerava app. You only pay for verified, intent-driven leads.
              </div>
            </div>
          </div>
        </div>
      )}

      {step === 'details' && (
        <div>
          <div className="mb-8">
            <h1 className="text-3xl text-neutral-900 mb-2">Create Exclusive</h1>
            <p className="text-neutral-600">
              Design a special offer for customers charging at your location
            </p>
          </div>

          {/* Billing status indicator */}
          {paymentStatus?.has_card && (
            <div className="mb-6 bg-green-50 border border-green-200 rounded-lg px-4 py-3 flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-800">
                Billing: Pay as you go &middot; {paymentStatus.card_brand} ****{paymentStatus.card_last4}
              </span>
            </div>
          )}

          <div className="max-w-3xl">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Name */}
              <div className="bg-white p-6 rounded-lg border border-neutral-200">
                <label className="block mb-2">
                  <span className="text-sm text-neutral-900">Exclusive Name</span>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    placeholder="e.g., Free Pastry with Coffee"
                    className="mt-1 w-full px-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                    required
                  />
                </label>
              </div>

              {/* Description */}
              <div className="bg-white p-6 rounded-lg border border-neutral-200">
                <label className="block mb-2">
                  <span className="text-sm text-neutral-900">What Customers Receive</span>
                  <textarea
                    value={formData.description}
                    onChange={(e) => handleChange('description', e.target.value)}
                    placeholder="Describe what the customer gets..."
                    rows={3}
                    className="mt-1 w-full px-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent resize-none"
                    required
                  />
                </label>
              </div>

              {/* Daily Cap */}
              <div className="bg-white p-6 rounded-lg border border-neutral-200">
                <label className="block">
                  <span className="text-sm text-neutral-900">Daily Activation Cap</span>
                  <input
                    type="number"
                    value={formData.dailyCap}
                    onChange={(e) => handleChange('dailyCap', e.target.value)}
                    min="1"
                    className="mt-1 w-full px-4 py-3 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:border-transparent"
                    required
                  />
                  <div className="mt-2 flex items-start gap-2 text-xs text-neutral-600">
                    <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
                    <span>Maximum number of customers who can activate this exclusive per day</span>
                  </div>
                </label>
              </div>

              {/* Pricing Note */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-start gap-2">
                  <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-sm text-blue-900 mb-1">Pricing</div>
                    <div className="text-xs text-blue-700">
                      {paymentStatus?.has_card
                        ? 'You\'ll be charged $1.50 per verified claim. Your card will be billed weekly for accumulated claims.'
                        : 'Each verified claim costs $1.00 from your campaign balance. Campaign auto-pauses when budget runs out.'
                      }
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => navigate('/exclusives')}
                  className="flex-1 border border-neutral-300 text-neutral-700 py-3 px-6 rounded-lg hover:bg-neutral-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-neutral-900 text-white py-3 px-6 rounded-lg hover:bg-neutral-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Publishing...' : 'Publish Exclusive'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
