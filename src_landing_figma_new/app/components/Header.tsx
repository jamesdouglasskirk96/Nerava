import { Button } from './Button';

export function Header() {
  return (
    <header className="w-full bg-white border-b border-border">
      <div className="max-w-7xl mx-auto px-6 md:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-foreground">Nerava</span>
            <span className="text-primary text-xl">⚡</span>
          </div>
          <nav className="hidden md:flex items-center gap-6">
            <a href="#how-it-works" className="text-foreground hover:text-muted-foreground transition-colors">
              How It Works
            </a>
            <a href="#for-charger-owners" className="text-foreground hover:text-muted-foreground transition-colors">
              For Charger Owners
            </a>
            <Button variant="primary" className="px-4 py-2">Get Started</Button>
          </nav>
        </div>
      </div>
    </header>
  );
}
