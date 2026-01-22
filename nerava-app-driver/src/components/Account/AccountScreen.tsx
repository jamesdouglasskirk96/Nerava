import { useNavigate } from 'react-router-dom'
import { ArrowLeft, User, Heart, Settings, HelpCircle, LogOut } from 'lucide-react'

export function AccountScreen() {
  const navigate = useNavigate()
  const isAuthenticated = !!localStorage.getItem('access_token')

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    navigate('/')
  }

  return (
    <div className="h-[100dvh] flex flex-col bg-white">
      {/* Header */}
      <header className="px-5 h-[60px] flex items-center border-b border-[#E4E6EB]">
        <button onClick={() => navigate(-1)} className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="ml-4 text-lg font-medium">Account</h1>
      </header>

      {/* Content */}
      <div className="flex-1 p-5 space-y-4">
        {/* Profile section */}
        <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center">
            <User className="w-8 h-8 text-gray-500" />
          </div>
          <div>
            <p className="font-medium text-[#050505]">
              {isAuthenticated ? 'Driver' : 'Guest'}
            </p>
            <p className="text-sm text-[#65676B]">
              {isAuthenticated ? 'Signed in' : 'Not signed in'}
            </p>
          </div>
        </div>

        {/* Menu items */}
        <div className="space-y-2">
          <button className="w-full flex items-center gap-3 p-4 hover:bg-gray-50 rounded-xl">
            <Heart className="w-5 h-5 text-[#65676B]" />
            <span>Favorites</span>
          </button>
          <button className="w-full flex items-center gap-3 p-4 hover:bg-gray-50 rounded-xl">
            <Settings className="w-5 h-5 text-[#65676B]" />
            <span>Settings</span>
          </button>
          <button className="w-full flex items-center gap-3 p-4 hover:bg-gray-50 rounded-xl">
            <HelpCircle className="w-5 h-5 text-[#65676B]" />
            <span>Help & Support</span>
          </button>
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 p-4 hover:bg-gray-50 rounded-xl text-red-500"
            >
              <LogOut className="w-5 h-5" />
              <span>Sign Out</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

