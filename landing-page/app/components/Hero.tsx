'use client'

import Image from 'next/image'
import { PrimaryButton, OutlineButton } from './Button'

export default function Hero() {
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const handleGetSavingsEstimate = () => {
    scrollToSection('impact-calculator')
  }

  const handleUploadUsageReport = () => {
    scrollToSection('how-it-works')
    // TODO: Could open a modal for file upload in future
  }

  return (
    <section className="bg-white py-12 sm:py-16 lg:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
          {/* Left Column - Text Content */}
          <div className="space-y-6">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
              Cut EV Charging Costs & Reward Your Drivers Automatically
            </h1>
            <p className="text-lg sm:text-xl text-gray-600 leading-relaxed">
              Nerava shifts EV charging to off-peak hours and turns the savings into driver perks.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <PrimaryButton onClick={handleGetSavingsEstimate}>
                Get Savings Estimate
              </PrimaryButton>
              <OutlineButton onClick={handleUploadUsageReport}>
                Upload Usage Report
              </OutlineButton>
            </div>
          </div>

          {/* Right Column - Image */}
          <div className="relative w-full h-[400px] sm:h-[500px] lg:h-[600px] rounded-lg overflow-hidden shadow-xl">
            {/* Placeholder for hero charger image - replace with actual image */}
            <div className="w-full h-full bg-gradient-to-br from-primary-soft to-primary-light flex items-center justify-center">
              <div className="text-center text-white/80">
                <svg className="w-24 h-24 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <p className="text-sm">Hero Charger Image</p>
                <p className="text-xs mt-1">/landing/hero-charger.png</p>
              </div>
            </div>
            {/* Uncomment when image is added:
            <Image
              src="/landing/hero-charger.png"
              alt="EV charging station with Nerava app interface"
              fill
              className="object-cover"
              priority
            />
            */}
          </div>
        </div>
      </div>
    </section>
  )
}

