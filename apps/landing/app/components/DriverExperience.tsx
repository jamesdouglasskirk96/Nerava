import Image from 'next/image'

export default function DriverExperience() {
  const steps = [
    {
      number: '1',
      title: 'Automatic Enrollment',
      description: 'Drivers are automatically enrolled when they charge at your location—no apps to download or accounts to create.',
    },
    {
      number: '2',
      title: 'Smart Notifications',
      description: 'Drivers receive timely alerts about optimal charging windows and available rewards.',
    },
    {
      number: '3',
      title: 'Earn Nova Tokens',
      description: 'Every off-peak charging session automatically earns Nova based on the energy savings generated.',
    },
    {
      number: '4',
      title: 'Instant Redemption',
      description: 'Drivers redeem Nova for branded digital gift cards—Starbucks, Amazon, Target, and more.',
    },
  ]

  return (
    <section className="bg-white py-16 sm:py-20 lg:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left Side - Image */}
          <div className="relative w-full h-[400px] sm:h-[500px] lg:h-[600px] rounded-lg overflow-hidden shadow-xl order-2 lg:order-1">
            <Image
              src="/landing/driver-experience.png"
              alt="Driver using Nerava app on mobile device"
              fill
              className="object-cover"
              placeholder="blur"
              blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAIAAoDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAhEAACAQMDBQAAAAAAAAAAAAABAgMABAUGIWGRkqGx0f/EABUBAQEAAAAAAAAAAAAAAAAAAAMF/8QAGhEAAgIDAAAAAAAAAAAAAAAAAAECEgMRkf/aAAwDAQACEQMRAD8AltJagyeH0AthI5xdrLcNM91BF5pX2HaH9bcfaSXWGaRmknyJckliyjqTzSlT54b6bk+h0R//2Q=="
            />
          </div>

          {/* Right Side - Content */}
          <div className="space-y-8 order-1 lg:order-2">
            <div>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4 break-words">
                The Complete Driver Experience
              </h2>
              <p className="text-lg text-gray-600">
                Nerava makes sustainable charging behavior rewarding and automatic for your drivers, members, or customers.
              </p>
            </div>

            {/* Steps List */}
            <div className="space-y-6">
              {steps.map((step, index) => (
                <div key={index} className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-primary text-white rounded-full flex items-center justify-center font-bold text-lg">
                      {step.number}
                    </div>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                      {step.title}
                    </h3>
                    <p className="text-gray-600">
                      {step.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

