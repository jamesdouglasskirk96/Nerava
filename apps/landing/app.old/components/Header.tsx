'use client'

export default function Header() {
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const scrollToContact = () => {
    scrollToSection('final-cta')
  }

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <a href="/" className="text-2xl font-bold text-primary flex items-center">
              Nerava
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="inline-block w-5 h-5 ml-1 text-primary"
              >
                <path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z" />
              </svg>
            </a>
          </div>
          <nav className="hidden md:flex items-center space-x-6">
            <a
              href="#how-it-works"
              onClick={(e) => {
                e.preventDefault()
                scrollToSection('how-it-works')
              }}
              className="text-gray-700 hover:text-primary transition-colors"
            >
              How It Works
            </a>
            <a
              href="#charger-owners"
              onClick={(e) => {
                e.preventDefault()
                scrollToSection('charger-owners')
              }}
              className="text-gray-700 hover:text-primary transition-colors"
            >
              For Charger Owners
            </a>
            <button
              onClick={scrollToContact}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            >
              Get Started
            </button>
          </nav>
          <div className="md:hidden">
            <button
              onClick={scrollToContact}
              className="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            >
              Contact
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

