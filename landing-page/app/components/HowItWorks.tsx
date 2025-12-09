'use client'

import { useState } from 'react'
import { OutlineButton } from './Button'

export default function HowItWorks() {
  const [fileSelected, setFileSelected] = useState(false)

  const steps = [
    {
      number: '01',
      title: 'Upload Usage Report',
      description: 'Simply upload your current charger usage data. Our system analyzes consumption patterns to identify peak load inefficiencies and savings opportunities.',
    },
    {
      number: '02',
      title: 'Nerava Rewards Behavior',
      description: 'We automatically incentivize your drivers to charge during off-peak hours. By shifting demand, we reduce your operational costs and grid strain significantly.',
    },
    {
      number: '03',
      title: 'Cycle Savings into Perks',
      description: 'You purchase Nova using a fraction of your realized savings. This creates a virtuous cycle where lower utility bills fund high-value driver amenities.',
    },
  ]

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFileSelected(true)
      // TODO: This is front-end only. No backend integration yet.
      // In production, this would upload to a backend endpoint.
      console.log('File selected:', e.target.files[0].name)
    }
  }

  return (
    <section id="how-it-works" className="bg-gray-50 py-16 sm:py-20 lg:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4 break-words">
            How Nerava Works
          </h2>
          <p className="text-lg text-gray-600">
            Our platform seamlessly integrates with your existing infrastructure to optimize energy usage without requiring any new hardware installations.
          </p>
        </div>

        {/* Three Steps */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12 mb-12">
          {steps.map((step, index) => (
            <div key={index} className="text-center">
              <div className="text-5xl font-bold text-primary mb-4">
                {step.number}
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">
                {step.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {step.description}
              </p>
              {index === 0 && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <label className="block">
                    <span className="sr-only">Upload usage report</span>
                    <input
                      type="file"
                      onChange={handleFileChange}
                      accept=".csv,.xlsx,.xls,.pdf"
                      className="hidden"
                      id="usage-report-upload"
                    />
                    <OutlineButton
                      onClick={() => document.getElementById('usage-report-upload')?.click()}
                      className="w-full"
                    >
                      {fileSelected ? 'File Selected ✓' : 'Upload Usage Report'}
                    </OutlineButton>
                  </label>
                  <p className="text-xs text-gray-500 mt-2 italic">
                    We'll walk you through this on our intro call
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

