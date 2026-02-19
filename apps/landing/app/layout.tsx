import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Header from './components/Header'
import Footer from './components/SiteFooter'
import { MobileRedirectBanner } from './components/MobileRedirectBanner'
import { ConsentBanner } from './components/ConsentBanner'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Nerava - Turn EV Charging into Local Discovery',
  description: 'Discover local restaurants, cafes, and experiences while your EV charges. Exclusive perks for drivers.',
  keywords: ['EV charging', 'electric vehicle', 'local discovery', 'restaurant deals', 'charging stations'],
  authors: [{ name: 'Nerava' }],
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://nerava.network',
    siteName: 'Nerava',
    title: 'Nerava - Turn EV Charging into Local Discovery',
    description: 'Discover local restaurants, cafes, and experiences while your EV charges. Exclusive perks for drivers.',
    images: [
      {
        url: 'https://nerava.network/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Nerava - EV Charging Discovery',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Nerava - Turn EV Charging into Local Discovery',
    description: 'Discover local restaurants, cafes, and experiences while your EV charges.',
    images: ['https://nerava.network/twitter-card.png'],
    creator: '@neaborhood',
  },
  robots: {
    index: true,
    follow: true,
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
  icons: {
    icon: '/favicon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Header />
        <main>{children}</main>
        <Footer />
        <MobileRedirectBanner />
        <ConsentBanner />
      </body>
    </html>
  )
}

