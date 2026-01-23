import Card from './Card'

export default function DecisionWindowSection() {
  const insights = [
    {
      title: '15–45 minutes of idle time',
      description: "Every charging session is a moment of opportunity. They're nearby, they have time, and they're ready to discover what's around them."
    },
    {
      title: 'Driver is already nearby',
      description: 'Businesses are within walking distance of chargers. No driving needed, just a short walk to discover something new.'
    },
    {
      title: 'High intent, low friction',
      description: "The right opportunity at the right moment—it's not passive browsing, it's a moment of active decision-making."
    },
    {
      title: 'Discovery gap today',
      description: "Most drivers don't know what's walkable nearby, leading to less optimal use of their most important resource: time."
    }
  ]

  return (
    <section id="decision-window" className="w-full py-20 md:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Charging creates a decision window
          </h2>
          <p className="text-lg text-muted-foreground">
            Every time an EV driver plugs in, a moment of opportunity opens. They're nearby, they have time, and they're ready to discover what's around them.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          {insights.map((insight, index) => (
            <Card key={index}>
              <h3 className="font-bold text-foreground mb-2">{insight.title}</h3>
              <p className="text-muted-foreground">{insight.description}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}



