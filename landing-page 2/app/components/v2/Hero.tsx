import { Button } from '../Button'
import { getDriverCTAHref, getMerchantCTAHref, getChargerOwnerCTAHref } from './ctaLinks'

export default function Hero() {
  return (
    <section className="w-full bg-[#E8F0FF] py-20 md:py-32">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-4">
            Nerava
          </h1>
          <h2 className="text-3xl md:text-5xl font-bold text-foreground mb-4">
            What to do while you charge.
          </h2>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Nerava connects EV drivers with walkable businesses during active charging sessions.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
            <Button variant="primary" href={getDriverCTAHref()}>
              Open Nerava
            </Button>
            <Button variant="primary" href={getMerchantCTAHref()}>
              For Businesses
            </Button>
          </div>
          <Button 
            variant="text" 
            href={getChargerOwnerCTAHref()}
            className="text-sm"
          >
            I'm a Charger Owner
          </Button>
        </div>
      </div>
    </section>
  )
}

