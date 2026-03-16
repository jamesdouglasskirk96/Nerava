'use client'

import { getMerchantCTAHref, getSponsorCTAHref, getDriverCTAHref } from './v2/ctaLinks'

export default function Footer() {
  return (
    <footer className="w-full bg-[#1a1a1a] text-white py-12">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div>
            <div className="mb-4">
              <img
                src="/nerava-logo.png"
                alt="Nerava"
                className="h-8 w-auto"
              />
            </div>
            <p className="text-gray-400 text-sm max-w-xs">
              The programmable incentive layer for EV charging. Earn rewards, discover deals, and get paid to drive electric.
            </p>
          </div>

          <div>
            <h3 className="font-bold mb-4">Platform</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a href={getDriverCTAHref()} className="hover:text-white transition-colors">
                  Driver App
                </a>
              </li>
              <li>
                <a href={getMerchantCTAHref()} className="hover:text-white transition-colors">
                  Merchant Portal
                </a>
              </li>
              <li>
                <a href={getSponsorCTAHref()} className="hover:text-white transition-colors">
                  Sponsor Console
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold mb-4">Company</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a href="/support" className="hover:text-white transition-colors">
                  Support
                </a>
              </li>
              <li>
                <a href="mailto:hello@nerava.network" className="hover:text-white transition-colors">
                  Contact
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold mb-4">Legal</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a href="/privacy" className="hover:text-white transition-colors">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="/terms" className="hover:text-white transition-colors">
                  Terms of Service
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-700 pt-8 text-center text-sm text-gray-400">
          &copy; {new Date().getFullYear()} Nerava, Inc. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
