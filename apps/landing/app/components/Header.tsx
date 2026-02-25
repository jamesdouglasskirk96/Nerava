'use client'

import { Button } from './Button'

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
    <header className="w-full bg-white border-b border-border">
      <div className="max-w-7xl mx-auto px-6 md:px-8 py-4">
        <div className="flex items-center justify-between">
          <a href="/" className="flex items-center">
            <img
              src="/nerava-logo.png"
              alt="Nerava"
              className="h-8 w-auto"
            />
          </a>
          <nav className="hidden md:flex items-center gap-6">
            <a
              href="#activates-moment"
              onClick={(e) => {
                e.preventDefault()
                scrollToSection('activates-moment')
              }}
              className="text-foreground hover:text-muted-foreground transition-colors"
            >
              How It Works
            </a>
            <a
              href="#built-to-scale"
              onClick={(e) => {
                e.preventDefault()
                scrollToSection('built-to-scale')
              }}
              className="text-foreground hover:text-muted-foreground transition-colors"
            >
              For Charger Owners
            </a>
            <Button
              variant="primary"
              onClick={scrollToContact}
              className="px-4 py-2"
            >
              Get in Touch
            </Button>
          </nav>
          <div className="md:hidden">
            <Button
              variant="primary"
              onClick={scrollToContact}
              className="px-3 py-1.5 text-sm"
            >
              Get in Touch
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}

