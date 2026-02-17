export const metadata = {
  title: 'Privacy Policy - Nerava',
  description: 'Privacy Policy for Nerava mobile app',
}

export default function PrivacyPolicy() {
  return (
    <main className="min-h-screen bg-white py-16 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
        <p className="text-gray-500 mb-8">Last updated: February 17, 2026</p>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Introduction</h2>
          <p className="text-gray-700 mb-4">
            Nerava ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and share information about you when you use our mobile application and services.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Information We Collect</h2>

          <h3 className="text-xl font-medium mb-2">Location Data</h3>
          <p className="text-gray-700 mb-4">
            We collect your device's location to detect nearby EV chargers and show you relevant merchant offers. Location data is only collected when you have the app open or have granted background location permission.
          </p>

          <h3 className="text-xl font-medium mb-2">Account Information</h3>
          <p className="text-gray-700 mb-4">
            When you create an account, we collect your phone number for verification purposes. You may optionally provide your email address and vehicle information.
          </p>

          <h3 className="text-xl font-medium mb-2">Usage Data</h3>
          <p className="text-gray-700 mb-4">
            We collect information about how you use the app, including charger visits, merchant interactions, and reward redemptions.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">How We Use Your Information</h2>
          <ul className="list-disc list-inside text-gray-700 space-y-2">
            <li>To provide and improve our services</li>
            <li>To detect nearby chargers and merchants</li>
            <li>To process reward redemptions</li>
            <li>To send you notifications about offers and updates</li>
            <li>To prevent fraud and abuse</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Information Sharing</h2>
          <p className="text-gray-700 mb-4">
            We do not sell your personal information. We may share your information with:
          </p>
          <ul className="list-disc list-inside text-gray-700 space-y-2">
            <li>Merchants when you redeem an offer (limited to information needed to fulfill the offer)</li>
            <li>Service providers who help us operate our services</li>
            <li>Law enforcement when required by law</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Data Retention</h2>
          <p className="text-gray-700 mb-4">
            We retain your information for as long as your account is active or as needed to provide services. You may request deletion of your account and associated data at any time.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Your Rights</h2>
          <p className="text-gray-700 mb-4">
            You have the right to:
          </p>
          <ul className="list-disc list-inside text-gray-700 space-y-2">
            <li>Access your personal data</li>
            <li>Request correction of inaccurate data</li>
            <li>Request deletion of your data</li>
            <li>Opt out of marketing communications</li>
            <li>Disable location services at any time</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Contact Us</h2>
          <p className="text-gray-700">
            If you have questions about this Privacy Policy, please contact us at:{' '}
            <a href="mailto:privacy@nerava.network" className="text-blue-600 hover:underline">
              privacy@nerava.network
            </a>
          </p>
        </section>
      </div>
    </main>
  )
}
