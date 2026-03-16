import { Button } from '../Button'
import { getMerchantFindHref, getSponsorCTAHref, getDriverCTAHref } from './ctaLinks'

export default function FinalCTA() {
  return (
    <section id="final-cta" className="w-full py-20 md:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-8">
            Join the charging network
          </h2>
          <p className="text-lg text-muted-foreground mb-10">
            Whether you drive, own a business, or sponsor campaigns — there's a place for you on Nerava.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
            <Button variant="primary" href={getDriverCTAHref()}>
              I'm a Driver
            </Button>
            <Button variant="secondary" href={getMerchantFindHref()}>
              I'm a Merchant
            </Button>
            <Button variant="secondary" href={getSponsorCTAHref()}>
              I'm a Sponsor
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            Questions? Reach us at <a href="mailto:hello@nerava.network" className="text-primary underline hover:opacity-80">hello@nerava.network</a>
          </p>
        </div>
      </div>
    </section>
  )
}
