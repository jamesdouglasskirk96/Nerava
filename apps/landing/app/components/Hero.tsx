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
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight break-words">
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
            <Image
              src="/landing/hero-charger.png"
              alt="EV charging station with Nerava app interface"
              fill
              className="object-cover"
              priority
              placeholder="blur"
              blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAIAAoDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAhEAACAQMDBQAAAAAAAAAAAAABAgMABAUGIWGRkqGx0f/EABUBAQEAAAAAAAAAAAAAAAAAAAMF/8QAGhEAAgIDAAAAAAAAAAAAAAAAAAECEgMRkf/aAAwDAQACEQMRAD8AltJagyeH0AthI5xdrLcNM91BF5pX2HaH9bcfaSXWGaRmknyJckliyjqTzSlT54b6bk+h0R//2Q=="
            />
          </div>
        </div>
      </div>
    </section>
  )
}

