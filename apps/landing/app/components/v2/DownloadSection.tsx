import { APP_STORE_URL, PLAY_STORE_URL, WEB_APP_URL } from './ctaLinks'

export default function DownloadSection() {
  return (
    <section id="download" className="w-full py-20 md:py-24 bg-[#E8F0FF]">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Start earning today
          </h2>
          <p className="text-lg text-muted-foreground mb-10">
            Download Nerava and turn your next charging session into rewards.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-8">
            <a
              href={APP_STORE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block"
            >
              <img
                src="/badges/app-store.svg"
                alt="Download on the App Store"
                className="h-12"
              />
            </a>
            <a
              href={PLAY_STORE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block"
            >
              <img
                src="/badges/play-store.svg"
                alt="Get it on Google Play"
                className="h-12"
              />
            </a>
          </div>
          <p className="text-sm text-muted-foreground">
            Or use the{' '}
            <a
              href={WEB_APP_URL}
              className="text-primary underline hover:opacity-80"
              target="_blank"
              rel="noopener noreferrer"
            >
              web app
            </a>
            {' '}— no download required.
          </p>
        </div>
      </div>
    </section>
  )
}
