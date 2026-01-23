import { Sparkles } from 'lucide-react'
import { ExclusiveInfoTooltip } from '../shared/ExclusiveInfoTooltip'

interface ExclusiveOfferCardProps {
  title: string
  description: string
  options?: string
}

export function ExclusiveOfferCard({ title, description, options }: ExclusiveOfferCardProps) {
  return (
    <div className="flex items-start gap-3 bg-amber-50 rounded-xl p-4 border border-amber-200">
      <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
        <Sparkles className="w-5 h-5 text-amber-600" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <p className="text-sm font-semibold text-amber-900">{title}</p>
          <ExclusiveInfoTooltip />
        </div>
        <p className="text-sm text-amber-800 mb-1">{description}</p>
        {options && (
          <p className="text-sm text-amber-600">{options}</p>
        )}
      </div>
    </div>
  )
}


