export const metadata = {
  title: 'Terms of Service - Nerava',
  description: 'Terms of Service for Nerava mobile app and platform',
}

export default function TermsOfService() {
  return (
    <main className="min-h-screen bg-white py-16 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        <p className="text-gray-500 mb-8">Last updated: March 11, 2026</p>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">1. Acceptance of Terms</h2>
          <p className="text-gray-700 mb-4">
            By accessing or using the Nerava mobile application, website, or any related services (collectively, the &ldquo;Service&rdquo;), you agree to be bound by these Terms of Service (&ldquo;Terms&rdquo;). If you do not agree to these Terms, do not use the Service.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">2. Description of Service</h2>
          <p className="text-gray-700 mb-4">
            Nerava is a platform that connects EV drivers with charging incentives, merchant deals, and reward programs. The Service includes a driver-facing mobile app, merchant portal, sponsor campaign console, and associated backend systems. Nerava verifies EV charging sessions and distributes rewards based on campaign rules set by sponsors.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">3. User Accounts</h2>
          <p className="text-gray-700 mb-4">
            You may need to create an account to access certain features of the Service. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You agree to provide accurate, current, and complete information during registration and to update such information to keep it accurate.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">4. Rewards and Payments</h2>
          <p className="text-gray-700 mb-4">
            Nerava may offer cash rewards, Nova points, and other incentives for verified charging sessions. Reward amounts, eligibility criteria, and availability are determined by active campaigns and may change at any time without notice. Rewards are subject to verification and may be withheld or revoked if fraudulent activity is detected.
          </p>
          <p className="text-gray-700 mb-4">
            Cash withdrawals are processed via Stripe and are subject to minimum withdrawal amounts and processing times. Nerava is not responsible for delays caused by third-party payment processors.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">5. Charging Session Verification</h2>
          <p className="text-gray-700 mb-4">
            Nerava verifies charging sessions using vehicle APIs (such as Tesla Fleet API), geolocation data, and other signals. By using the Service, you consent to the collection and processing of this data for session verification and reward distribution. Attempting to falsify or manipulate charging data is a violation of these Terms and may result in account termination.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">6. Location Data</h2>
          <p className="text-gray-700 mb-4">
            The Service uses your device&rsquo;s location to detect nearby chargers, verify charging sessions, and surface relevant merchant deals. You may control location permissions through your device settings, but some features may not function without location access. See our <a href="/privacy" className="text-blue-600 underline">Privacy Policy</a> for details on how location data is collected and used.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">7. Prohibited Conduct</h2>
          <p className="text-gray-700 mb-4">You agree not to:</p>
          <ul className="list-disc list-inside text-gray-700 mb-4 space-y-2">
            <li>Use the Service for any unlawful purpose</li>
            <li>Attempt to falsify charging sessions or manipulate reward systems</li>
            <li>Create multiple accounts to circumvent per-driver caps or limits</li>
            <li>Interfere with or disrupt the Service or its infrastructure</li>
            <li>Reverse engineer, decompile, or disassemble the Service</li>
            <li>Use automated scripts or bots to interact with the Service</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">8. Account Deletion</h2>
          <p className="text-gray-700 mb-4">
            You may delete your account at any time through the Account section of the app. Upon deletion, your personal data will be removed in accordance with our Privacy Policy. Any pending rewards or unredeemed Nova points will be forfeited upon account deletion.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">9. Intellectual Property</h2>
          <p className="text-gray-700 mb-4">
            The Service and its original content, features, and functionality are owned by Nerava, Inc. and are protected by copyright, trademark, and other intellectual property laws. You may not copy, modify, distribute, or create derivative works based on the Service without our express written permission.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">10. Disclaimer of Warranties</h2>
          <p className="text-gray-700 mb-4">
            The Service is provided &ldquo;as is&rdquo; and &ldquo;as available&rdquo; without warranties of any kind, either express or implied. Nerava does not guarantee that the Service will be uninterrupted, error-free, or secure. Reward availability depends on active campaigns and may be discontinued at any time.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">11. Limitation of Liability</h2>
          <p className="text-gray-700 mb-4">
            To the maximum extent permitted by law, Nerava, Inc. shall not be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits or revenues, whether incurred directly or indirectly, or any loss of data, use, or goodwill.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">12. Changes to Terms</h2>
          <p className="text-gray-700 mb-4">
            We reserve the right to modify these Terms at any time. We will notify users of material changes by updating the &ldquo;Last updated&rdquo; date. Your continued use of the Service after changes constitutes acceptance of the modified Terms.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">13. Contact</h2>
          <p className="text-gray-700 mb-4">
            If you have questions about these Terms, contact us at{' '}
            <a href="mailto:hello@nerava.network" className="text-blue-600 underline">
              hello@nerava.network
            </a>.
          </p>
        </section>
      </div>
    </main>
  )
}
