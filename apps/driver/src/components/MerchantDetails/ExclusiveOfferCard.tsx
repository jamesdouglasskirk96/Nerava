import { Gift } from 'lucide-react'

interface ExclusiveOfferCardProps {
  title: string
  description: string
  options?: string
}

export function ExclusiveOfferCard({ title, description, options }: ExclusiveOfferCardProps) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
          <Gift className="w-5 h-5 text-blue-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-blue-600">{title || 'Exclusive Offer'}</p>
          <p className="text-sm text-gray-900">{description}</p>
          {options && (
            <p className="text-sm text-gray-600 mt-0.5">{options}</p>
          )}
        </div>
      </div>
    </div>
  )
}


