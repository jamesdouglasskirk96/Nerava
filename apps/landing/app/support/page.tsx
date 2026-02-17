export const metadata = {
  title: 'Support - Nerava',
  description: 'Get help with Nerava',
}

export default function Support() {
  return (
    <main className="min-h-screen bg-white py-16 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Support</h1>

        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">Contact Us</h2>
          <p className="text-gray-700 mb-4">
            Need help? We're here for you.
          </p>
          <p className="text-gray-700">
            Email:{' '}
            <a href="mailto:support@nerava.network" className="text-blue-600 hover:underline">
              support@nerava.network
            </a>
          </p>
        </section>

        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-6">Frequently Asked Questions</h2>

          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-2">How does Nerava work?</h3>
              <p className="text-gray-700">
                Nerava automatically detects when you're at an EV charger and shows you exclusive offers from nearby restaurants and businesses. Simply check in to redeem your reward while your car charges.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-2">Which chargers are supported?</h3>
              <p className="text-gray-700">
                We currently support Tesla Superchargers in Austin, TX. We're expanding to more locations and charger networks soon.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-2">Why do you need my location?</h3>
              <p className="text-gray-700">
                We use your location to detect when you're at a supported charger and to show you relevant nearby offers. You can disable location access at any time in your device settings.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-2">How do I redeem an offer?</h3>
              <p className="text-gray-700">
                When you're at a supported charger, open the app and tap on a merchant offer. Press "Check In" to generate your reward code, then show it to the merchant when you order.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-2">Is Nerava free?</h3>
              <p className="text-gray-700">
                Yes! Nerava is completely free to use. Merchants sponsor the rewards you receive.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-2">How do I delete my account?</h3>
              <p className="text-gray-700">
                To delete your account and all associated data, please email{' '}
                <a href="mailto:support@nerava.network" className="text-blue-600 hover:underline">
                  support@nerava.network
                </a>{' '}
                with the subject "Account Deletion Request".
              </p>
            </div>
          </div>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Report an Issue</h2>
          <p className="text-gray-700">
            Found a bug or having technical issues? Please email us at{' '}
            <a href="mailto:support@nerava.network" className="text-blue-600 hover:underline">
              support@nerava.network
            </a>{' '}
            with a description of the problem and we'll get back to you as soon as possible.
          </p>
        </section>
      </div>
    </main>
  )
}
