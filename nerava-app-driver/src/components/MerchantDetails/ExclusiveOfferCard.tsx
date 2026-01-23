import { Wallet } from 'lucide-react'

interface ExclusiveOfferCardProps {
  title: string
  description: string
  options?: string
}

export function ExclusiveOfferCard({ title, description, options }: ExclusiveOfferCardProps) {
  return (
    <div className="bg-gradient-to-r from-yellow-500/10 to-amber-500/10 rounded-xl p-3 border border-yellow-600/20">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 bg-yellow-500/20 rounded-full flex items-center justify-center flex-shrink-0">
          <Wallet className="w-4 h-4 text-yellow-700" />
        </div>
        <div className="flex-1">
          <h3 className="font-medium text-sm mb-0.5 text-yellow-900">{title}</h3>
          <p className="text-sm text-yellow-800 leading-relaxed">
            {description}
          </p>
          {options && (
            <p className="text-xs text-yellow-700 mt-1">
              {options}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

