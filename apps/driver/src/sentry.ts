import * as Sentry from '@sentry/react'

const dsn = import.meta.env.VITE_SENTRY_DSN

if (dsn) {
  Sentry.init({
    dsn,
    environment: import.meta.env.VITE_ENV || 'development',
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0.1,
    beforeSend(event) {
      // Scrub auth tokens from breadcrumbs
      if (event.breadcrumbs) {
        event.breadcrumbs = event.breadcrumbs.map((b) => {
          if (b.data?.headers) {
            delete b.data.headers['Authorization']
          }
          return b
        })
      }
      return event
    },
  })
}
