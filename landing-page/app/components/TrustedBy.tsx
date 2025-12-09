export default function TrustedBy() {
  // Placeholder logos - replace with actual property type icons
  const propertyIcons = [
    { name: 'Apartments', icon: '🏢' },
    { name: 'Hotels', icon: '🏨' },
    { name: 'Offices', icon: '🏢' },
    { name: 'Gyms', icon: '💪' },
    { name: 'Retail', icon: '🛒' },
  ]

  return (
    <section className="bg-gray-50 py-16 sm:py-20 lg:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-4xl mx-auto">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            Trusted by Modern Properties
          </h2>
          <p className="text-lg text-gray-600 mb-12">
            Join forward-thinking property managers and business owners who are turning energy efficiency into a competitive advantage.
          </p>

          {/* Property Icons */}
          <div className="flex flex-wrap justify-center items-center gap-8 mb-12">
            {propertyIcons.map((property, index) => (
              <div key={index} className="flex flex-col items-center">
                <div className="w-16 h-16 bg-white rounded-lg shadow-md flex items-center justify-center text-3xl mb-2">
                  {property.icon}
                </div>
                <span className="text-sm text-gray-600">{property.name}</span>
              </div>
            ))}
          </div>

          {/* Testimonial */}
          <div className="bg-white p-8 rounded-lg shadow-md max-w-2xl mx-auto">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-primary" fill="currentColor" viewBox="0 0 32 32">
                  <path d="M10 8c-3.3 0-6 2.7-6 6v10h10V14H8c0-1.1.9-2 2-2V8zm16 0c-3.3 0-6 2.7-6 6v10h10V14h-6c0-1.1.9-2 2-2V8z" />
                </svg>
              </div>
              <blockquote className="ml-4 text-lg text-gray-700 italic">
                "Finally—a charging amenity drivers actually use. It paid for itself in the first month through demand-charge reductions alone."
              </blockquote>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

