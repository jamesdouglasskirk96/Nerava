import { useNavigate } from 'react-router-dom';
import { Chrome } from 'lucide-react';

export function ClaimBusiness() {
  const navigate = useNavigate();

  const handleContinue = () => {
    navigate('/claim/location');
  };

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-xl shadow-sm border border-neutral-200 p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl text-neutral-900 mb-2">Claim your business on Nerava</h1>
          <p className="text-neutral-600">
            Connect with your Google Business Profile to get started
          </p>
        </div>

        <button
          onClick={handleContinue}
          className="w-full bg-neutral-900 text-white py-4 px-6 rounded-lg hover:bg-neutral-800 transition-colors flex items-center justify-center gap-3"
        >
          <Chrome className="w-5 h-5" />
          Continue with Google
        </button>

        <div className="mt-6 p-4 bg-neutral-50 rounded-lg">
          <p className="text-sm text-neutral-600 text-center">
            <strong className="text-neutral-900">No cost to claim. No commitment.</strong>
            <br />
            We'll verify your business through your Google Business Profile.
          </p>
        </div>

        <div className="mt-6 text-center text-xs text-neutral-500">
          By continuing, you agree to Nerava's Terms of Service and Privacy Policy
        </div>
      </div>
    </div>
  );
}
