import { Button } from '../Button'
import { getMerchantFindHref, getChargerOwnerCTAHref } from './ctaLinks'

export default function FinalCTA() {
  return (
    <section id="final-cta" className="w-full py-20 md:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-8">
            Be part of the charging moment
          </h2>
          <p className="text-lg text-muted-foreground mb-10">
            Join the network that's transforming idle charging time into local discovery and commerce.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
            <Button variant="primary" href={getMerchantFindHref()}>
              I'm a Merchant
            </Button>
            <Button variant="secondary" href={getChargerOwnerCTAHref()}>
              I'm a Charger Owner
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            Interested in sponsoring charging incentives? <a href="mailto:sponsors@nerava.network" className="text-primary underline hover:opacity-80">sponsors@nerava.network</a>
          </p>
        </div>
      </div>
    </section>
  )
}

