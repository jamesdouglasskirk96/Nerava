import Card from './Card'

export default function DriversSection() {
  const benefits = [
    {
      title: 'Earn while you charge',
      description: 'Get cash rewards and Nova points for every verified charging session. Campaigns from sponsors pay you for charging at specific stations and times.'
    },
    {
      title: 'Track your sessions',
      description: 'Automatic Tesla integration detects when you plug in. Track energy delivered, session history, and climb the Bronze to Platinum reputation tiers.'
    },
    {
      title: 'Discover local deals',
      description: 'Find coffee shops, restaurants, and stores within walking distance of your charger. Exclusive merchant deals unlock while you charge.'
    },
    {
      title: 'Get paid to your wallet',
      description: 'Withdraw your earnings anytime. Cash goes straight to your bank via Stripe. No minimums to start earning, no subscriptions.'
    },
  ]

  return (
    <section id="drivers" className="w-full py-20 md:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            The driver experience
          </h2>
          <p className="text-lg text-muted-foreground">
            Plug in, earn rewards, discover deals nearby. Nerava works in the background so you can make the most of every charge.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          {benefits.map((benefit, index) => (
            <Card key={index}>
              <h3 className="font-bold text-foreground mb-2">{benefit.title}</h3>
              <p className="text-muted-foreground">{benefit.description}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
