import Image from 'next/image'

export default function HighTrafficVenues() {
  const venues = [
    {
      title: 'Grocery Stores',
      description: 'Incentivize shoppers to charge during slower hours, reducing peak demand while increasing dwell time and basket size.',
    },
    {
      title: 'Co-Working Spaces',
      description: 'Reward members for off-peak charging with workspace credits, creating a sustainable community culture.',
    },
    {
      title: 'Universities',
      description: 'Manage campus charging demand across student, faculty, and visitor populations with automated incentives.',
    },
    {
      title: 'Retail Centers',
      description: 'Turn charging stations into customer loyalty tools by offering store credits for strategic charging times.',
    },
  ]

  return (
    <section className="bg-white py-16 sm:py-20 lg:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left Column - Content */}
          <div className="space-y-8">
            <div>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4 break-words">
                Perfect for High-Traffic Venues
              </h2>
            </div>

            {/* Venue Cards */}
            <div className="space-y-6">
              {venues.map((venue, index) => (
                <div key={index} className="bg-gray-50 p-6 rounded-lg">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    {venue.title}
                  </h3>
                  <p className="text-gray-600">
                    {venue.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column - Image */}
          <div className="relative w-full h-[400px] sm:h-[500px] lg:h-[600px] rounded-lg overflow-hidden shadow-xl">
            {/* Placeholder for high-traffic image */}
            <div className="w-full h-full bg-gradient-to-br from-primary-soft to-primary-light flex items-center justify-center">
              <div className="text-center text-white/80">
                <svg className="w-24 h-24 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <p className="text-sm">High Traffic Venues Image</p>
                <p className="text-xs mt-1">/landing/high-traffic.png</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

