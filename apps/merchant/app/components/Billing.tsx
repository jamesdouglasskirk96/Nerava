import { useState, useEffect } from 'react';
import { Check, Loader2, ExternalLink, FileText, CreditCard, Shield } from 'lucide-react';
import {
  createSubscription, getSubscription, cancelSubscription,
  getBillingPortalUrl, getInvoices, getPaymentStatus, setupCard, removeCard,
  type Invoice, type PaymentStatus,
} from '../services/api';

export function Billing() {
  const [subscription, setSubscription] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [invoicesLoading, setInvoicesLoading] = useState(false);
  const [portalLoading, setPortalLoading] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | null>(null);
  const [cardLoading, setCardLoading] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const success = params.get('success');
    const cardSaved = params.get('card_saved');

    Promise.all([
      getSubscription().catch(() => null),
      getPaymentStatus().catch(() => null),
    ]).then(([subData, pmData]) => {
      setSubscription(subData?.subscription || null);
      setPaymentStatus(pmData);
      if (subData?.subscription) {
        setInvoicesLoading(true);
        getInvoices()
          .then((data) => setInvoices(data?.invoices || []))
          .catch(() => {})
          .finally(() => setInvoicesLoading(false));
      }
    }).finally(() => setLoading(false));

    if (success === 'true' || cardSaved === 'true') {
      // Refresh after Stripe redirect
      if (cardSaved === 'true') {
        window.history.replaceState({}, '', window.location.pathname);
      }
      setTimeout(() => {
        getSubscription().then((data) => setSubscription(data?.subscription || null)).catch(() => {});
        getPaymentStatus().then(setPaymentStatus).catch(() => {});
      }, 2000);
    }
  }, []);

  const handleUpgrade = async () => {
    setActionLoading(true);
    try {
      const placeId = localStorage.getItem('place_id') || '';
      const { checkout_url } = await createSubscription(placeId, 'pro');
      window.location.href = checkout_url;
    } catch (err: any) {
      alert(err.message || 'Failed to start checkout');
    } finally {
      setActionLoading(false);
    }
  };

  const handleManageBilling = async () => {
    setPortalLoading(true);
    try {
      const { url } = await getBillingPortalUrl();
      window.open(url, '_blank');
    } catch (err: any) {
      alert(err.message || 'Failed to open billing portal');
    } finally {
      setPortalLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Cancel your Pro subscription? You will keep access until the end of this billing period.')) return;
    setActionLoading(true);
    try {
      await cancelSubscription();
      setSubscription({ ...subscription, canceled_at: new Date().toISOString() });
    } catch (err: any) {
      alert(err.message || 'Failed to cancel');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddCard = async () => {
    setCardLoading(true);
    try {
      const { checkout_url } = await setupCard();
      window.location.href = checkout_url;
    } catch (err: any) {
      alert(err.message || 'Failed to start card setup');
    } finally {
      setCardLoading(false);
    }
  };

  const handleRemoveCard = async () => {
    if (!confirm('Remove your card? Pay-as-you-go exclusives will stop working.')) return;
    setCardLoading(true);
    try {
      await removeCard();
      setPaymentStatus((prev) => prev ? { ...prev, has_card: false, card_last4: null, card_brand: null, billing_type: 'free' } : null);
    } catch (err: any) {
      alert(err.message || 'Failed to remove card');
    } finally {
      setCardLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-neutral-400" />
      </div>
    );
  }

  const isProActive = subscription?.plan === 'pro' && subscription?.status === 'active';
  const isCanceled = !!subscription?.canceled_at;

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-neutral-900">Billing</h2>
        <p className="text-sm text-neutral-500 mt-1">Manage your payment method and plan</p>
      </div>

      {/* Card on File Section */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Payment Method</h3>
        {paymentStatus?.has_card ? (
          <div className="bg-white rounded-xl border border-neutral-200 p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-2.5 bg-green-50 rounded-lg">
                  <CreditCard className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-sm font-medium text-neutral-900">
                    {paymentStatus.card_brand} ending in {paymentStatus.card_last4}
                  </div>
                  <div className="text-xs text-neutral-500 mt-0.5 flex items-center gap-1">
                    <Shield className="w-3 h-3" />
                    Pay as you go &middot; $1.50 per verified claim
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleAddCard}
                  disabled={cardLoading}
                  className="text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50"
                >
                  Update
                </button>
                <button
                  onClick={handleRemoveCard}
                  disabled={cardLoading}
                  className="text-sm text-red-600 hover:text-red-700 disabled:opacity-50"
                >
                  Remove
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl border-2 border-dashed border-neutral-300 p-6 text-center">
            <CreditCard className="w-8 h-8 text-neutral-400 mx-auto mb-3" />
            <p className="text-sm text-neutral-600 mb-1">No payment method on file</p>
            <p className="text-xs text-neutral-500 mb-4">Add a card to enable pay-as-you-go billing for exclusives</p>
            <button
              onClick={handleAddCard}
              disabled={cardLoading}
              className="inline-flex items-center gap-2 bg-neutral-900 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-neutral-800 transition-colors disabled:opacity-50"
            >
              {cardLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}
              {cardLoading ? 'Redirecting...' : 'Add Card'}
            </button>
          </div>
        )}
      </div>

      {/* Pro subscription banner */}
      {isProActive && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-5 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-green-800 font-medium">Pro Plan Active</span>
              {subscription.current_period_end && (
                <p className="text-sm text-green-700 mt-1">
                  {isCanceled
                    ? `Cancels on ${new Date(subscription.current_period_end).toLocaleDateString()}`
                    : `Next billing: ${new Date(subscription.current_period_end).toLocaleDateString()}`}
                </p>
              )}
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleManageBilling}
                disabled={portalLoading}
                className="text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50 flex items-center gap-1"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                {portalLoading ? 'Opening...' : 'Manage Billing'}
              </button>
              {!isCanceled && (
                <button
                  onClick={handleCancel}
                  disabled={actionLoading}
                  className="text-sm text-red-600 hover:text-red-700 disabled:opacity-50"
                >
                  Cancel Plan
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Plans */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">Plans</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Free Tier */}
          <div className="rounded-xl border border-neutral-200 bg-white p-6 flex flex-col">
            <h3 className="text-lg font-semibold text-neutral-900">Free</h3>
            <div className="mt-2 mb-3">
              <span className="text-3xl font-bold text-neutral-900">$0</span>
              <span className="text-neutral-500 text-sm">/month</span>
            </div>
            <p className="text-sm text-neutral-500 mb-5">
              Essential tools to get started with EV drivers
            </p>
            <ul className="space-y-2.5 mb-6 flex-1">
              {[
                'Business listing on Nerava',
                'Aggregate charging insights',
                '1 EV reward / exclusive deal',
                'Weekly email report',
                'QR code check-in',
              ].map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm text-neutral-700">
                  <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
            <div className="text-center py-2.5 px-4 rounded-lg text-sm font-medium bg-neutral-100 text-neutral-500">
              {isProActive ? 'Included' : 'Current Plan'}
            </div>
          </div>

          {/* Pro Tier */}
          <div className="rounded-xl border-2 border-blue-500 bg-white p-6 flex flex-col ring-1 ring-blue-500">
            <span className="text-xs font-medium text-blue-600 bg-blue-50 rounded-full px-2.5 py-0.5 self-start mb-3">
              Recommended
            </span>
            <h3 className="text-lg font-semibold text-neutral-900">Pro</h3>
            <div className="mt-2 mb-3">
              <span className="text-3xl font-bold text-neutral-900">$200</span>
              <span className="text-neutral-500 text-sm">/month per location</span>
            </div>
            <p className="text-sm text-neutral-500 mb-5">
              Full analytics and customer insights to grow your business
            </p>
            <ul className="space-y-2.5 mb-6 flex-1">
              {[
                'Everything in Free',
                'Session-level detail in Insights',
                'Customer visit frequency analytics',
                'Unlimited EV rewards / exclusives',
                'Priority support',
                'Walk traffic & dwell time reports',
              ].map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm text-neutral-700">
                  <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
            {isProActive ? (
              <div className="text-center py-2.5 px-4 rounded-lg text-sm font-medium bg-green-100 text-green-700">
                Active
              </div>
            ) : (
              <button
                onClick={handleUpgrade}
                disabled={actionLoading}
                className="block text-center py-2.5 px-4 rounded-lg text-sm font-medium bg-neutral-900 text-white hover:bg-neutral-800 transition-colors disabled:opacity-50"
              >
                {actionLoading ? 'Redirecting...' : 'Upgrade to Pro'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Invoice History */}
      {(invoices.length > 0 || invoicesLoading) && (
        <div>
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">Invoice History</h3>
          {invoicesLoading ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="w-5 h-5 animate-spin text-neutral-400" />
            </div>
          ) : (
            <div className="rounded-xl border border-neutral-200 bg-white overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-neutral-100 bg-neutral-50">
                    <th className="text-left py-3 px-4 font-medium text-neutral-600">Date</th>
                    <th className="text-left py-3 px-4 font-medium text-neutral-600">Amount</th>
                    <th className="text-left py-3 px-4 font-medium text-neutral-600">Status</th>
                    <th className="text-right py-3 px-4 font-medium text-neutral-600">Invoice</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((inv) => (
                    <tr key={inv.id} className="border-b border-neutral-50 last:border-0">
                      <td className="py-3 px-4 text-neutral-700">
                        {new Date(inv.created * 1000).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-neutral-900 font-medium">
                        ${(inv.amount_due / 100).toFixed(2)}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            inv.status === 'paid'
                              ? 'bg-green-50 text-green-700'
                              : inv.status === 'open'
                                ? 'bg-yellow-50 text-yellow-700'
                                : 'bg-neutral-100 text-neutral-600'
                          }`}
                        >
                          {inv.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {inv.hosted_invoice_url && (
                          <a
                            href={inv.hosted_invoice_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-700 inline-flex items-center gap-1"
                          >
                            <FileText className="w-3.5 h-3.5" />
                            View
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
