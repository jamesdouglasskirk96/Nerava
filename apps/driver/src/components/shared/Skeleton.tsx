// Skeleton shimmer loading components
// Used as placeholder content while data is loading

interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
}

/** A single shimmer block - use for text lines, images, badges, etc. */
export function Skeleton({ className = '', variant = 'rectangular' }: SkeletonProps) {
  const baseClasses = 'skeleton-shimmer bg-[#E4E6EB]'
  const variantClasses = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg'
  }

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={{
        animationDuration: '1.5s',
        animationTimingFunction: 'ease-in-out'
      }}
      aria-hidden="true"
    />
  )
}

/** Skeleton for a charger card (PreChargingScreen, Layer 1) */
export function ChargerCardSkeleton() {
  return (
    <div className="rounded-xl overflow-hidden bg-white shadow-lg" aria-hidden="true">
      <div className="p-4">
        {/* Header row */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <Skeleton className="h-6 w-3/4 mb-2" />
            <Skeleton className="h-4 w-1/3" />
          </div>
          <Skeleton className="h-7 w-24 rounded-full" />
        </div>
        {/* Stall dots */}
        <div className="flex gap-1 mt-3 mb-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="w-2 h-2 rounded-full" />
          ))}
          <Skeleton className="h-4 w-16 ml-2" />
        </div>
        {/* Details row */}
        <div className="flex gap-4 mt-2">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-12" />
        </div>
        {/* Nearby experience placeholder */}
        <div className="mt-4 pt-3 border-t border-[#E4E6EB]">
          <Skeleton className="h-4 w-32 mb-2" />
          <Skeleton className="h-24 w-full rounded-lg" />
        </div>
        {/* CTA button */}
        <Skeleton className="h-12 w-full rounded-lg mt-3" />
      </div>
    </div>
  )
}

/** Skeleton for the merchant carousel (Layer 2) */
export function MerchantCarouselSkeleton() {
  return (
    <div className="relative h-full flex flex-col justify-start pt-2 px-5" aria-hidden="true">
      {/* Featured card */}
      <div className="mb-3">
        <div className="bg-[#F7F8FA] rounded-2xl overflow-hidden border border-[#E4E6EB]">
          <Skeleton className="h-44 w-full rounded-none" />
          <div className="p-4">
            <Skeleton className="h-7 w-3/4 mb-2" />
            <Skeleton className="h-4 w-1/2 mb-2" />
            <Skeleton className="h-4 w-1/3" />
          </div>
        </div>
      </div>
      {/* Secondary cards */}
      <div className="grid grid-cols-2 gap-3">
        {[0, 1].map((i) => (
          <div key={i} className="bg-[#F7F8FA] rounded-2xl overflow-hidden border border-[#E4E6EB]">
            <Skeleton className="h-[123px] w-full rounded-none" />
            <div className="p-3">
              <Skeleton className="h-5 w-3/4 mb-2" />
              <Skeleton className="h-6 w-20 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/** Skeleton for merchant card (matches merchant card layout) */
export function MerchantCardSkeleton() {
  return (
    <div className="bg-white rounded-2xl overflow-hidden shadow-sm" aria-hidden="true">
      <Skeleton className="h-32 w-full" />
      <div className="p-4 space-y-2">
        <Skeleton variant="text" className="w-3/4" />
        <Skeleton variant="text" className="w-1/2" />
        <div className="flex gap-2 mt-3">
          <Skeleton className="h-6 w-16 rounded-full" />
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
      </div>
    </div>
  )
}

/** Skeleton for merchant details screen (Layer 3) */
export function MerchantDetailsSkeleton() {
  return (
    <div className="bg-white" style={{ height: 'var(--app-height, 100dvh)' }} aria-hidden="true">
      {/* Hero image */}
      <Skeleton className="w-full h-64 rounded-none" />
      {/* Content */}
      <div className="px-4 py-6 space-y-5">
        <div>
          <Skeleton className="h-9 w-3/4 mb-3" />
          <Skeleton className="h-5 w-1/3 mb-3" />
          <Skeleton className="h-6 w-48 rounded-full" />
        </div>
        {/* Offer card */}
        <div className="rounded-xl p-5 border border-gray-200">
          <Skeleton className="h-5 w-1/2 mb-2" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4 mt-1" />
        </div>
        {/* Distance card */}
        <div className="rounded-xl p-5 border border-gray-200">
          <Skeleton className="h-5 w-1/3 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </div>
        {/* Hours card */}
        <div className="rounded-xl p-5 border border-gray-200">
          <Skeleton className="h-5 w-1/4 mb-2" />
          <Skeleton className="h-4 w-2/3" />
        </div>
        {/* CTA button */}
        <Skeleton className="h-12 w-full rounded-lg" />
      </div>
    </div>
  )
}
