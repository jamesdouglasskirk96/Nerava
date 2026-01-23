'use client'

export default function Footer() {
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }
  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2">
            <h3 className="text-white text-xl font-bold mb-4">Nerava</h3>
            <p className="text-sm mb-4 max-w-md">
              Cut EV charging costs and reward your drivers automatically. 
              Transform energy efficiency into a competitive advantage.
            </p>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Platform</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a 
                  href="#how-it-works" 
                  onClick={(e) => {
                    e.preventDefault()
                    scrollToSection('how-it-works')
                  }}
                  className="hover:text-white transition-colors"
                >
                  How It Works
                </a>
              </li>
              {process.env.NEXT_PUBLIC_ADMIN_URL && (
                <li>
                  <a 
                    href={process.env.NEXT_PUBLIC_ADMIN_URL}
                    className="hover:text-white transition-colors opacity-50"
                    title="Internal admin portal"
                  >
                    Admin
                  </a>
                </li>
              )}
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-2 text-sm">
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
                  href="mailto:contact@nerava.com"
                  className="hover:text-white transition-colors"
                >
                  Contact
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-8 pt-8 border-t border-gray-800 text-sm text-center">
          <p>&copy; {new Date().getFullYear()} Nerava. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}

