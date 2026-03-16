import { useState, useRef } from 'react'
import { X, Camera, Upload, Loader2 } from 'lucide-react'
import { Button } from '../shared/Button'

interface ReceiptUploadModalProps {
  isOpen: boolean
  merchantName: string
  claimId: string
  remainingSeconds: number
  onClose: () => void
  onUpload: (imageBase64: string) => Promise<void>
}

export function ReceiptUploadModal({
  isOpen,
  merchantName,
  claimId: _claimId,
  remainingSeconds,
  onClose,
  onUpload,
}: ReceiptUploadModalProps) {
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  if (!isOpen) return null

  const remainingMinutes = Math.max(0, Math.ceil(remainingSeconds / 60))

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      setError('Please select an image file')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('Image must be under 10MB')
      return
    }

    setError(null)
    const reader = new FileReader()
    reader.onload = () => {
      setPreview(reader.result as string)
    }
    reader.readAsDataURL(file)
  }

  const handleUpload = async () => {
    if (!preview) return
    setUploading(true)
    setError(null)
    try {
      await onUpload(preview)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40">
      <div className="w-full max-w-lg bg-white rounded-t-3xl p-6 pb-8 animate-slide-up">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-xl font-semibold text-[#050505]">Upload Receipt</h3>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <p className="text-sm text-[#65676B] mb-4">
          Take a photo of your receipt from <span className="font-medium text-[#050505]">{merchantName}</span> to verify your visit.
        </p>

        {remainingMinutes > 0 && (
          <div className="bg-amber-50 rounded-xl px-4 py-2.5 mb-4 text-sm text-amber-700 text-center">
            {remainingMinutes} minutes remaining to upload
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={handleFileSelect}
        />

        {preview ? (
          <div className="mb-4">
            <img
              src={preview}
              alt="Receipt preview"
              className="w-full max-h-64 object-contain rounded-xl border border-[#E4E6EB]"
            />
            <button
              onClick={() => {
                setPreview(null)
                if (fileInputRef.current) fileInputRef.current.value = ''
              }}
              className="text-sm text-[#1877F2] mt-2 hover:underline"
            >
              Retake photo
            </button>
          </div>
        ) : (
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full border-2 border-dashed border-[#E4E6EB] rounded-xl py-10 flex flex-col items-center gap-3 mb-4 hover:border-[#1877F2] transition-colors"
          >
            <Camera className="w-10 h-10 text-[#65676B]" />
            <span className="text-sm text-[#65676B]">Tap to take a photo or upload</span>
          </button>
        )}

        {error && (
          <div className="bg-red-50 text-red-700 text-sm rounded-xl px-4 py-2.5 mb-4">
            {error}
          </div>
        )}

        <Button
          variant="primary"
          className="w-full"
          onClick={handleUpload}
          disabled={!preview || uploading}
        >
          {uploading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Upload className="w-4 h-4" />
              Upload Receipt
            </span>
          )}
        </Button>
      </div>
    </div>
  )
}
