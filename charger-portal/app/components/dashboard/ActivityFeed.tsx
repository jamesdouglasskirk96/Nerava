import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'
import type { ActivityItem } from '@/lib/types/dashboard'

interface ActivityFeedProps {
  activity: ActivityItem[]
  isLoading?: boolean
}

export function ActivityFeed({ activity, isLoading = false }: ActivityFeedProps) {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)

    if (diffHours < 1) return 'Just now'
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  if (isLoading) {
    return (
      <Card className="animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <h3 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h3>
      <div className="space-y-4 max-h-[500px] overflow-y-auto">
        {activity.map((item) => (
          <div key={item.id} className="flex gap-3 pb-4 border-b border-gray-100 last:border-0">
            <div className="flex-shrink-0">
              <Badge variant={item.type}>{item.type}</Badge>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900">{item.description}</p>
              <p className="text-xs text-gray-500 mt-1">{formatTimestamp(item.timestamp)}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

