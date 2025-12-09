import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Header from './components/Header'
import Footer from './components/SiteFooter'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Nerava — The EV Commerce Network | Charge anywhere. Spend everywhere.',
  description: "Get rewarded for smart charging and spend Nova at participating merchants. Whether you're an EV driver looking to maximize your charging value or a merchant seeking new customers, Nerava connects sustainable charging behavior with local commerce.",
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
      </body>
    </html>
  )
}

