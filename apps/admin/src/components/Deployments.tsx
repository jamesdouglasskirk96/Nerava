import { useState } from 'react'
import { Rocket, RefreshCw, AlertTriangle } from 'lucide-react'
import { fetchAPI } from '../services/api'

interface DeployTarget {
  id: string
  name: string
  description: string
  lastDeploy?: string
}

const DEPLOY_TARGETS: DeployTarget[] = [
  { id: 'backend', name: 'Backend API', description: 'App Runner service' },
  { id: 'driver', name: 'Driver App', description: 'S3 + CloudFront' },
  { id: 'admin', name: 'Admin Portal', description: 'S3 + CloudFront' },
  { id: 'merchant', name: 'Merchant Portal', description: 'S3 + CloudFront' },
]

export function Deployments() {
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null)
  const [isDeploying, setIsDeploying] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const handleTriggerDeploy = async () => {
    if (!selectedTarget) return
    setIsDeploying(true)
    setFeedback(null)

    try {
      const data = await fetchAPI<{ workflow: string }>('/v1/admin/deployments/trigger', {
        method: 'POST',
        body: JSON.stringify({ target: selectedTarget, ref: 'main' }),
      })
      setFeedback({ type: 'success', message: `Deployment triggered successfully! Workflow: ${data.workflow}` })
      setTimeout(() => setFeedback(null), 5000)
      setShowConfirm(false)
      setSelectedTarget(null)
    } catch (e: any) {
      const errorMessage = e.message || (e instanceof Error ? e.message : 'Unknown error')
      setFeedback({ type: 'error', message: `Failed to trigger deployment: ${errorMessage}` })
      setTimeout(() => setFeedback(null), 5000)
    } finally {
      setIsDeploying(false)
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <Rocket className="w-6 h-6 text-blue-600" />
        <h1 className="text-2xl font-bold">Deployments</h1>
      </div>

      {feedback && (
        <div
          className={`mb-4 border rounded-lg p-4 ${
            feedback.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-700'
              : 'bg-red-50 border-red-200 text-red-700'
          }`}
        >
          {feedback.message}
        </div>
      )}

      <div className="grid gap-4">
        {DEPLOY_TARGETS.map(target => (
          <div
            key={target.id}
            className={`p-4 border rounded-lg cursor-pointer transition ${
              selectedTarget === target.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => setSelectedTarget(target.id)}
          >
            <h3 className="font-medium">{target.name}</h3>
            <p className="text-sm text-gray-500">{target.description}</p>
          </div>
        ))}
      </div>

      <button
        onClick={() => setShowConfirm(true)}
        disabled={!selectedTarget || isDeploying}
        className="mt-6 w-full py-3 bg-blue-600 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isDeploying ? 'Deploying...' : 'Deploy Selected'}
      </button>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-xl max-w-sm">
            <div className="flex items-center gap-2 text-amber-600 mb-4">
              <AlertTriangle className="w-5 h-5" />
              <h3 className="font-semibold">Confirm Deployment</h3>
            </div>
            <p className="text-gray-600 mb-6">
              Deploy {DEPLOY_TARGETS.find(t => t.id === selectedTarget)?.name} to production? This cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 py-2 border rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleTriggerDeploy}
                className="flex-1 py-2 bg-blue-600 text-white rounded-lg"
              >
                Deploy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}




