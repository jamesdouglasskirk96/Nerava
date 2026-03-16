import { Button } from '../Button'
import { getDriverCTAHref, getMerchantCTAHref } from './ctaLinks'

export default function Hero() {
  return (
    <section className="w-full bg-[#E8F0FF] py-20 md:py-32">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-4">
            Charge. Earn. Redeem.
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Nerava turns every EV charging session into rewards. Earn cash and Nova points while you charge, discover local deals, and get paid for driving electric.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
            <Button variant="primary" href={getDriverCTAHref()}>
              Get the App
            </Button>
            <Button variant="secondary" href={getMerchantCTAHref()}>
              For Business
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            Available on iOS, Android, and the web
          </p>
        </div>
      </div>
    </section>
  )
}
