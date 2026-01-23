'use client'

import { getChargerOwnerCTAHref } from './v2/ctaLinks'

export default function Footer() {
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <footer className="w-full bg-[#1a1a1a] text-white py-12">
      <div className="max-w-7xl mx-auto px-6 md:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl font-bold">Nerava</span>
              <span className="text-primary text-xl">⚡</span>
            </div>
            <p className="text-gray-400 text-sm max-w-xs">
              What to do while you charge. Nerava connects EV drivers with walkable businesses during active charging sessions.
            </p>
          </div>
          
          <div>
            <h3 className="font-bold mb-4">Platform</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a 
                  href="#activates-moment" 
                  onClick={(e) => {
                    e.preventDefault()
                    scrollToSection('activates-moment')
                  }}
                  className="hover:text-white transition-colors"
                >
                  How It Works
                </a>
              </li>
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
              <li>
                <a 
                  href={getChargerOwnerCTAHref()}
                  className="hover:text-white transition-colors"
                >
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
              <li>
                <a 
                  href={getChargerOwnerCTAHref()}
                  className="hover:text-white transition-colors"
                >
                  Contact
                </a>
              </li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-700 pt-8 text-center text-sm text-gray-400">
          © {new Date().getFullYear()} Nerava. All rights reserved.
        </div>
      </div>
    </footer>
  )
}

