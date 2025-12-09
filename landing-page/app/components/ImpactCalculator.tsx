'use client'

import { useState } from 'react'
import { PrimaryButton } from './Button'

export default function ImpactCalculator() {
  const [chargers, setChargers] = useState(10)
  const [sessionsPerMonth, setSessionsPerMonth] = useState(200)

  // PLACEHOLDER FORMULA - DO NOT USE FOR REAL BILLING
  // This is a simple deterministic formula for demonstration only
  const estimatedMonthlySavings = Math.round(chargers * sessionsPerMonth * 0.5)
  const avgDriverPerkValue = Math.round(estimatedMonthlySavings * 0.1)

  const handleGetFullReport = () => {
    // Redirect to charger usage report form
    window.location.href = 'https://forms.gle/2HY3p3882yhqMkT69'
  }

  return (
    <section id="impact-calculator" className="bg-white py-16 sm:py-20 lg:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
            Calculate Your Potential Impact
          </h2>
          <p className="text-lg text-gray-600">
            See what happens when you optimize for off-peak charging. Based on a typical property with 10 chargers and 200 sessions per month, here&apos;s the value you could unlock immediately.
          </p>
        </div>

        {/* Interactive Calculator Form */}
        <div className="max-w-2xl mx-auto bg-gray-50 p-8 rounded-lg shadow-md mb-12">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div>
              <label htmlFor="chargers" className="block text-sm font-semibold text-gray-700 mb-2">
                Number of Chargers
              </label>
              <input
                id="chargers"
                type="number"
                min="1"
                max="100"
                value={chargers}
                onChange={(e) => setChargers(parseInt(e.target.value) || 1)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
            <div>
              <label htmlFor="sessions" className="block text-sm font-semibold text-gray-700 mb-2">
                Sessions per Month
              </label>
              <input
                id="sessions"
                type="number"
                min="1"
                max="10000"
                value={sessionsPerMonth}
                onChange={(e) => setSessionsPerMonth(parseInt(e.target.value) || 1)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>
          <p className="text-xs text-gray-500 text-center italic mb-6">
            Note: This is a placeholder calculation for demonstration only. Actual savings will vary based on your specific usage patterns and local utility rates.
          </p>
        </div>

        {/* Impact Numbers */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto mb-12">
          <div className="text-center">
            <div className="text-5xl sm:text-6xl font-bold text-primary mb-2">
              ${(estimatedMonthlySavings / 1000).toFixed(1)}K
            </div>
            <div className="text-xl font-semibold text-gray-900 mb-1">
              Estimated Monthly Savings
            </div>
            <div className="text-gray-600">
              Reduction in demand charges per month
            </div>
          </div>

          <div className="text-center">
            <div className="text-5xl sm:text-6xl font-bold text-primary mb-2">
              ${avgDriverPerkValue}
            </div>
            <div className="text-xl font-semibold text-gray-900 mb-1">
              Avg. Driver Perk Value
            </div>
            <div className="text-gray-600">
              Annual value returned to each EV driver in gift cards
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <PrimaryButton onClick={handleGetFullReport}>
            Get Your Full Savings Report
          </PrimaryButton>
        </div>
      </div>
    </section>
  )
}

