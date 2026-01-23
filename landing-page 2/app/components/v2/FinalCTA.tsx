import { Button } from '../Button'
import { getDriverCTAHref, getMerchantCTAHref, getChargerOwnerCTAHref } from './ctaLinks'

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
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="primary" href={getDriverCTAHref()}>
              I'm a Driver
            </Button>
            <Button variant="primary" href={getMerchantCTAHref()}>
              I'm a Merchant Near a Charger
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}

