import Image from 'next/image'
import SectionWrapper from './SectionWrapper'
import { PrimaryButton, SecondaryButton } from '../Button'

export default function Hero() {
  return (
    <div className="relative min-h-[90vh] flex items-center w-full">
      <div className="absolute inset-0 z-0">
          <Image
            src="/landing/v2/1_Nerava-The-EV-Commerce-Network.png"
            alt="EV charging station"
            fill
            className="object-cover"
            priority
          />
        <div className="absolute inset-0 bg-black/40" />
      </div>
      
      <div className="relative z-10 w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-4xl">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-4 break-words">
          Nerava — The EV Commerce Network
        </h1>
        <p className="text-xl sm:text-2xl lg:text-3xl text-white/90 mb-6 font-medium">
          Charge anywhere. Spend everywhere.
        </p>
        <p className="text-lg sm:text-xl text-white/90 mb-8 max-w-2xl">
          Get rewarded for smart charging and spend Nova at participating merchants. 
          Whether you're an EV driver looking to maximize your charging value or a merchant 
          seeking new customers, Nerava connects sustainable charging behavior with local commerce.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <PrimaryButton 
            href="#drivers"
            className="w-full sm:w-auto"
          >
            Get rewards for smart charging
          </PrimaryButton>
          <SecondaryButton 
            href="#merchants"
            className="w-full sm:w-auto bg-white/10 backdrop-blur-sm border-white text-white hover:bg-white/20"
          >
            Start accepting Nova
          </SecondaryButton>
        </div>
        
        <p className="text-sm text-white/80">
          Are you a charger owner or property manager?{' '}
          <a 
            href="#charger-owners" 
            className="underline hover:text-white transition-colors"
          >
            Get a free usage report analysis
          </a>
        </p>
        </div>
      </div>
    </div>
  )
}

