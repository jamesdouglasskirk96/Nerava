export default function ActivatesChargingMomentSection() {
  const steps = [
    {
      title: 'Detects active charging',
      description: "Nerava is constantly aware when you're charging, so you don't have to think about it."
    },
    {
      title: 'Surfaces nearby walkable businesses',
      description: 'See coffee shops, restaurants, and stores within walking distance of your charger.'
    },
    {
      title: 'Helps drivers decide instantly',
      description: 'No searching, no scrolling. The question "what should I do?" gets answered in one tap.'
    }
  ]

  return (
    <section id="activates-moment" className="w-full py-20 md:py-24 bg-secondary">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Nerava activates the charging moment
          </h2>
          <p className="text-lg text-muted-foreground">
            We turn idle charging time into discovery opportunities by connecting drivers with nearby businesses—right when it matters most.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {steps.map((step, index) => (
            <div key={index} className="text-center">
              <div className="mb-4">
                <div className="w-12 h-12 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xl font-bold mx-auto">
                  {index + 1}
                </div>
              </div>
              <h3 className="font-bold text-foreground mb-2">{step.title}</h3>
              <p className="text-muted-foreground">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}



