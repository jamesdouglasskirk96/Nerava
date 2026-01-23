import { useState } from 'react'
import { updateBrandImage } from '../services/api'

interface BrandImageUploadProps {
  merchantId: string
  currentImageUrl?: string
  onSuccess?: () => void
}

export function BrandImageUpload({ merchantId, currentImageUrl, onSuccess }: BrandImageUploadProps) {
  const [imageUrl, setImageUrl] = useState(currentImageUrl || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!imageUrl.trim()) {
      setError('Image URL is required')
      return
    }

    setLoading(true)
    setError(null)

    try {
      await updateBrandImage(merchantId, imageUrl.trim())
      if (onSuccess) onSuccess()
    } catch (err: any) {
      setError(err.message || 'Failed to update brand image')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white p-6 rounded-lg border border-neutral-200">
      <h3 className="text-lg font-semibold mb-4">Brand Image</h3>
      <p className="text-sm text-neutral-600 mb-4">
        Upload a custom brand image that will be shown instead of Google Places photos.
      </p>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            Image URL
          </label>
          <input
            type="url"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            placeholder="https://example.com/brand-image.jpg"
            className="w-full px-4 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
          />
          <p className="text-xs text-neutral-500 mt-1">
            Enter a publicly accessible image URL
          </p>
        </div>

        {currentImageUrl && (
          <div>
            <p className="text-sm font-medium mb-2">Current Image:</p>
            <img
              src={currentImageUrl}
              alt="Current brand image"
              className="w-32 h-32 object-cover rounded-lg border border-neutral-200"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none'
              }}
            />
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="bg-neutral-900 text-white px-6 py-2 rounded-lg hover:bg-neutral-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Saving...' : 'Save Brand Image'}
        </button>
      </form>
    </div>
  )
}




