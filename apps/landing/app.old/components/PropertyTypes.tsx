export default function PropertyTypes() {
  const propertyTypes = [
    {
      title: 'Apartments',
      description: 'Transform EV charging from a cost center into a driver retention tool.',
      example: '$20 monthly coffee credit for off-peak chargers.',
    },
    {
      title: 'Hotels & Hospitality',
      description: 'Encourage overnight charging to reduce daytime load.',
      example: 'Dining vouchers or loyalty points for guests.',
    },
    {
      title: 'Corporate Offices',
      description: 'Manage morning arrival spikes by incentivizing staggered charging.',
      example: 'Local lunch gift cards for employees.',
    },
    {
      title: 'Gyms & Health Clubs',
      description: 'Align charging with workout schedules to optimize turnover.',
      example: 'Smoothie bar credits or merch discounts.',
    },
  ]

  return (
    <section className="bg-gray-50 py-16 sm:py-20 lg:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4 break-words">
            Tailored for Every Property Type
          </h2>
          <p className="text-lg text-gray-600">
            Whether you manage long-term residences or high-traffic venues, Nerava adapts to your specific charging patterns and driver needs.
          </p>
        </div>

        {/* Property Type Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
          {propertyTypes.map((property, index) => (
            <div key={index} className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                {property.title}
              </h3>
              <p className="text-gray-600 mb-4">
                {property.description}
              </p>
              <div className="pt-4 border-t border-gray-200">
                <p className="text-sm font-semibold text-primary mb-1">Example Perk:</p>
                <p className="text-sm text-gray-600">{property.example}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

