'use client'

import { useState } from 'react'

interface NavItem {
  id: string
  label: string
  icon?: React.ReactNode
}

interface SidebarProps {
  activeNavItem?: string
}

const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'nova-budgets', label: 'Nova Budgets' },
  { id: 'drivers', label: 'Drivers' },
  { id: 'reports', label: 'Reports' },
  { id: 'settings', label: 'Settings' },
]

export function Sidebar({ activeNavItem = 'overview' }: SidebarProps) {
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  return (
    <>
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-4 left-4 z-40">
        <button
          onClick={() => setIsMobileOpen(!isMobileOpen)}
          className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          aria-label="Toggle sidebar"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
      </div>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-gray-600 bg-opacity-75 z-30"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full w-64 bg-white border-r border-gray-200 z-30
          transform transition-transform duration-300 ease-in-out
          lg:translate-x-0
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center mr-3">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <span className="text-2xl font-bold text-primary">Nerava</span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            {navItems.map((item) => (
              <button
                key={item.id}
                className={`
                  w-full text-left px-4 py-3 rounded-lg transition-colors
                  ${
                    activeNavItem === item.id
                      ? 'bg-primary-soft text-primary font-semibold'
                      : 'text-gray-700 hover:bg-gray-100'
                  }
                `}
              >
                {item.label}
              </button>
            ))}
          </nav>

          {/* Close button for mobile */}
          <div className="lg:hidden p-4 border-t border-gray-200">
            <button
              onClick={() => setIsMobileOpen(false)}
              className="w-full px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
            >
              Close Menu
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}

