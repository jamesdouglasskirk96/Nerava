export default function NovaEconomy() {
  const economySteps = [
    { label: 'Buy Nova Budget', description: 'Charger owner purchases Nova using a slice of savings' },
    { label: 'Fund Treasury', description: 'Budget moves into Nova treasury' },
    { label: 'Earn Nova', description: 'Drivers earn for off-peak charging sessions' },
    { label: 'Instant Redemption', description: 'Drivers redeem for branded cards' },
  ]

  return (
    <section className="bg-white py-16 sm:py-20 lg:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left Column - Content */}
          <div className="space-y-6">
            <div>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-2 break-words">
                The Nova Economy
              </h2>
              <h3 className="text-xl sm:text-2xl text-primary font-semibold mb-6">
                Digital Currency for Energy Savings
              </h3>
            </div>
            
            <p className="text-lg text-gray-600">
              Nova is the digital currency used to reward off-peak charging. It creates a seamless value flow from energy savings directly into driver wallets.
            </p>
            
            <p className="text-lg text-gray-600">
              Drivers redeem instantly through branded digital cards like Starbucks, Amazon, and Target—making sustainable charging behavior rewarding and effortless.
            </p>
          </div>

          {/* Right Column - Circular Diagram */}
          <div className="relative w-full h-[400px] sm:h-[500px] flex items-center justify-center">
            <div className="relative w-full h-full max-w-md mx-auto">
              {/* Central Circle */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-48 h-48 sm:w-56 sm:h-56 bg-primary text-white rounded-full flex flex-col items-center justify-center text-center p-6 shadow-xl z-10">
                  <h4 className="font-bold text-lg sm:text-xl mb-2">Nova Economy</h4>
                  <p className="text-xs sm:text-sm text-primary-soft">Seamless value flow from savings to wallets</p>
                </div>
              </div>

              {/* Steps around the circle */}
              {economySteps.map((step, index) => {
                const angle = (index * 90 - 90) * (Math.PI / 180)
                const radius = 140
                const x = Math.cos(angle) * radius
                const y = Math.sin(angle) * radius
                
                return (
                  <div
                    key={index}
                    className="absolute"
                    style={{
                      left: `calc(50% + ${x}px)`,
                      top: `calc(50% + ${y}px)`,
                      transform: 'translate(-50%, -50%)',
                      width: '140px',
                    }}
                  >
                    <div className="bg-white border-2 border-primary p-3 rounded-lg shadow-md text-center">
                      <div className="text-xs font-bold text-primary mb-1">{step.label}</div>
                      <div className="text-xs text-gray-600">{step.description}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

