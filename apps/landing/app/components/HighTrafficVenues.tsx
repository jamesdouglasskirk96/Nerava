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
            <Image
              src="/landing/high-traffic.png"
              alt="High traffic venue with EV charging stations"
              fill
              className="object-cover"
              placeholder="blur"
              blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAIAAoDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAhEAACAQMDBQAAAAAAAAAAAAABAgMABAUGIWGRkqGx0f/EABUBAQEAAAAAAAAAAAAAAAAAAAMF/8QAGhEAAgIDAAAAAAAAAAAAAAAAAAECEgMRkf/aAAwDAQACEQMRAD8AltJagyeH0AthI5xdrLcNM91BF5pX2HaH9bcfaSXWGaRmknyJckliyjqTzSlT54b6bk+h0R//2Q=="
            />
          </div>
        </div>
      </div>
    </section>
  )
}

