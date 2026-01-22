import { User } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface UserAvatarProps {
  onClick?: () => void
  className?: string
}

export function UserAvatar({ onClick, className = '' }: UserAvatarProps) {
  const navigate = useNavigate()

  const handleClick = () => {
    if (onClick) {
      onClick()
    } else {
      navigate('/account')
    }
  }

  return (
    <button
      onClick={handleClick}
      className={`w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center hover:bg-gray-200 active:scale-95 transition-all ${className}`}
      aria-label="Account"
    >
      <User className="w-5 h-5 text-[#050505]" />
    </button>
  )
}

