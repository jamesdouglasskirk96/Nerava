import { Button } from '../Button'
import Card from './Card'
import { getSponsorCTAHref } from './ctaLinks'

export default function SponsorsSection() {
  const benefits = [
    {
      title: 'Target by location and time',
      description: 'Create campaigns that reward drivers for charging at specific stations, networks, or zones — during the hours you choose.'
    },
    {
      title: 'Budget controls built in',
      description: 'Set total budget, per-driver caps, and daily limits. Atomic budget tracking ensures you never overspend.'
    },
    {
      title: 'Verified sessions only',
      description: 'Every session is verified through Tesla Fleet API and geolocation. Anti-fraud scoring ensures you pay for real charging, not fake claims.'
    }
  ]

  return (
    <section id="sponsors" className="w-full py-20 md:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            For sponsors and energy partners
          </h2>
          <p className="text-lg text-muted-foreground">
            Create campaigns that incentivize charging behavior. Reward drivers for charging at the right place, at the right time — and only pay for verified sessions.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mb-12">
          {benefits.map((benefit, index) => (
            <Card key={index}>
              <h3 className="font-bold text-foreground mb-2">{benefit.title}</h3>
              <p className="text-muted-foreground">{benefit.description}</p>
            </Card>
          ))}
        </div>
        <div className="text-center">
          <Button variant="primary" href={getSponsorCTAHref()}>
            Create a Campaign
          </Button>
        </div>
      </div>
    </section>
  )
}
