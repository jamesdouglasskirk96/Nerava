export default function WhyNeravaWorksSection() {
  const principles = [
    {
      title: 'High-intent',
      description: "Drivers are actively charging and looking for ways to spend their time. This isn't passive browsing—it's a moment of active decision-making."
    },
    {
      title: 'Proximity',
      description: 'Businesses are within walking distance of chargers. No driving needed, just a short walk to discover something new.'
    },
    {
      title: 'Zero friction',
      description: 'No search required, no scrolling through endless options. Nerava surfaces the right businesses at the right moment.'
    }
  ]

  return (
    <section id="why-works" className="w-full py-20 md:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Why Nerava Works
          </h2>
          <p className="text-lg text-muted-foreground mb-12">
            Three principles that make the charging moment perfect for local discovery
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 max-w-5xl mx-auto">
          {principles.map((principle, index) => (
            <div key={index} className="text-center">
              <h3 className="text-xl font-bold text-primary mb-3">{principle.title}</h3>
              <p className="text-muted-foreground">{principle.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}



