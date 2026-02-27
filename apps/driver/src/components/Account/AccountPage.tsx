import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Heart, LogOut, ChevronRight, X, User, Mail, Car, LogIn, Bell, BellOff, Ruler, ExternalLink, HelpCircle, Zap } from 'lucide-react'
import { useFavorites } from '../../contexts/FavoritesContext'
import { ShareNerava } from './ShareNerava'
import { LoginModal } from './LoginModal'
import { useTeslaStatus } from '../../services/api'

interface UserProfile {
  name?: string
  email?: string
  phone?: string
  vehicle?: string
  memberSince?: string
}

const NOTIFICATIONS_KEY = 'nerava_notifications_enabled'
const DISTANCE_UNIT_KEY = 'nerava_distance_unit'

export function AccountPage({ onClose }: { onClose: () => void }) {
  const { favorites, favoriteDetails, toggleFavorite, getMerchantName } = useFavorites()
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [showFavoritesList, setShowFavoritesList] = useState(false)
  const [showShareNerava, setShowShareNerava] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const navigate = useNavigate()

  // Preferences state
  const [notificationsEnabled, setNotificationsEnabled] = useState(() => {
    return localStorage.getItem(NOTIFICATIONS_KEY) !== 'false'
  })
  const [distanceUnit, setDistanceUnit] = useState<'miles' | 'km'>(() => {
    return (localStorage.getItem(DISTANCE_UNIT_KEY) as 'miles' | 'km') || 'miles'
  })

  // Tesla connection status
  const { data: teslaStatus, isLoading: teslaLoading } = useTeslaStatus()

  const checkAuth = () => {
    const token = localStorage.getItem('access_token')
    const storedUser = localStorage.getItem('nerava_user')

    if (token && storedUser) {
      setIsAuthenticated(true)
      try {
        const user = JSON.parse(storedUser)
        setUserProfile({
          name: user.name || 'EV Driver',
          email: user.email,
          phone: user.phone ? `***-***-${user.phone.slice(-4)}` : undefined,
          vehicle: user.vehicle || 'Tesla Owner',
          memberSince: user.created_at ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : 'January 2024',
        })
      } catch {
        setUserProfile({ name: 'EV Driver' })
      }
    } else {
      setIsAuthenticated(false)
      setUserProfile(null)
    }
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('nerava_user')
    window.location.reload()
  }

  const handleViewMerchant = (merchantId: string) => {
    onClose()
    navigate(`/merchant/${merchantId}`)
  }

  const handleRemoveFavorite = async (e: React.MouseEvent, merchantId: string) => {
    e.stopPropagation()
    await toggleFavorite(merchantId)
  }

  // Get display name from favorites context (with fallback formatting)
  const formatMerchantId = (id: string) => getMerchantName(id)

  // Generate referral code from user profile
  const referralCode = `NERAVA-EV-${new Date().getFullYear()}`

  const handleLoginSuccess = () => {
    checkAuth()
    setShowLoginModal(false)
  }

  const handleToggleNotifications = () => {
    const newValue = !notificationsEnabled
    setNotificationsEnabled(newValue)
    localStorage.setItem(NOTIFICATIONS_KEY, String(newValue))
  }

  const handleToggleDistanceUnit = () => {
    const newValue = distanceUnit === 'miles' ? 'km' : 'miles'
    setDistanceUnit(newValue)
    localStorage.setItem(DISTANCE_UNIT_KEY, newValue)
  }

  const handleConnectTesla = async () => {
    try {
      const { api } = await import('../../services/api')
      const response = await api.get<{ authorization_url: string }>('/v1/auth/tesla/connect')
      window.location.href = response.authorization_url
    } catch (e) {
      console.error('Failed to start Tesla connection:', e)
    }
  }

  if (showShareNerava) {
    return <ShareNerava onClose={() => setShowShareNerava(false)} referralCode={referralCode} />
  }

  return (
    <>
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onSuccess={handleLoginSuccess}
      />
    <div className="fixed inset-0 bg-white z-50 flex flex-col">
      <header className="flex items-center p-4 border-b border-[#E4E6EB]">
        <button onClick={showFavoritesList ? () => setShowFavoritesList(false) : onClose} className="p-2 -ml-2 hover:bg-gray-100 rounded-full">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="flex-1 text-center font-semibold text-lg">
          {showFavoritesList ? 'Favorites' : 'Account'}
        </h1>
        <div className="w-10" />
      </header>

      {showFavoritesList ? (
        <div className="flex-1 overflow-y-auto">
          {favorites.size === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 p-8">
              <Heart className="w-12 h-12 mb-4 text-gray-300" />
              <p className="text-center">No favorites yet</p>
              <p className="text-sm text-center mt-2">Tap the heart icon on any merchant to save it here</p>
            </div>
          ) : (
            <div className="divide-y">
              {Array.from(favorites).map((merchantId) => {
                const details = favoriteDetails.get(merchantId)
                return (
                  <div
                    key={merchantId}
                    onClick={() => handleViewMerchant(merchantId)}
                    className="flex items-center p-4 hover:bg-gray-50 active:bg-gray-100 cursor-pointer"
                  >
                    {details?.photo_url ? (
                      <img
                        src={details.photo_url}
                        alt={details.name}
                        className="w-10 h-10 rounded-full object-cover mr-3"
                      />
                    ) : (
                      <div className="w-10 h-10 bg-[#1877F2]/10 rounded-full flex items-center justify-center mr-3">
                        <Heart className="w-5 h-5 text-[#1877F2] fill-current" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{formatMerchantId(merchantId)}</p>
                      <p className="text-sm text-gray-500">{details?.category || 'Tap to view details'}</p>
                    </div>
                    <button
                      onClick={(e) => handleRemoveFavorite(e, merchantId)}
                      className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                    <ChevronRight className="w-5 h-5 text-gray-400 ml-1" />
                  </div>
                )
              })}
            </div>
          )}
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Profile Card or Sign In */}
          {isAuthenticated && userProfile ? (
            <div className="bg-blue-50 rounded-2xl p-5 border border-blue-100">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 bg-[#1877F2] rounded-full flex items-center justify-center">
                  <User className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">{userProfile.name}</h2>
                  <p className="text-sm text-[#65676B]">Member since {userProfile.memberSince}</p>
                </div>
              </div>

              {userProfile.email && (
                <div className="flex items-center gap-3 mb-2">
                  <Mail className="w-4 h-4 text-[#65676B]" />
                  <span className="text-sm text-[#050505]">{userProfile.email}</span>
                </div>
              )}

              {userProfile.vehicle && (
                <div className="flex items-center gap-3">
                  <Car className="w-4 h-4 text-[#65676B]" />
                  <span className="text-sm text-[#050505]">{userProfile.vehicle}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gradient-to-br from-[#1877F2] to-[#0d5bbf] rounded-2xl p-6 text-white">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                  <User className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">Welcome to Nerava</h2>
                  <p className="text-sm text-white/80">Sign in to unlock all features</p>
                </div>
              </div>

              <ul className="text-sm text-white/90 space-y-2 mb-5">
                <li className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Connect your Tesla account
                </li>
                <li className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Earn rewards while charging
                </li>
                <li className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Save your favorite merchants
                </li>
              </ul>

              <button
                onClick={() => setShowLoginModal(true)}
                className="w-full py-3 bg-white text-[#1877F2] font-semibold rounded-xl hover:bg-white/90 transition-colors flex items-center justify-center gap-2"
              >
                <LogIn className="w-5 h-5" />
                Sign In
              </button>
            </div>
          )}

          {/* Connected Vehicles */}
          {isAuthenticated && (
            <div className="bg-gray-50 rounded-2xl border border-[#E4E6EB] overflow-hidden">
              <div className="p-4 border-b border-[#E4E6EB]">
                <h3 className="font-semibold text-sm text-[#65676B] uppercase tracking-wide">Connected Vehicles</h3>
              </div>
              <div className="p-4">
                {teslaLoading ? (
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-200 rounded-full animate-pulse" />
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-32 animate-pulse mb-1" />
                      <div className="h-3 bg-gray-200 rounded w-24 animate-pulse" />
                    </div>
                  </div>
                ) : teslaStatus?.connected ? (
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-green-50 rounded-full flex items-center justify-center">
                      <Zap className="w-5 h-5 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-[#050505]">
                        {teslaStatus.vehicle_name || 'Tesla'}
                      </p>
                      <p className="text-sm text-[#65676B]">
                        {teslaStatus.vehicle_model || 'Connected'}
                        {teslaStatus.vin ? ` \u00B7 \u2022\u2022\u2022\u2022${teslaStatus.vin.slice(-4)}` : ''}
                      </p>
                    </div>
                    <div className="px-2.5 py-1 bg-green-100 rounded-full">
                      <span className="text-xs font-medium text-green-700">Connected</span>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={handleConnectTesla}
                    className="w-full flex items-center gap-3 p-1 hover:bg-gray-100 rounded-xl transition-colors"
                  >
                    <div className="w-10 h-10 bg-red-50 rounded-full flex items-center justify-center">
                      <Zap className="w-5 h-5 text-red-500" />
                    </div>
                    <div className="flex-1 text-left">
                      <p className="font-medium text-[#050505]">Connect Tesla</p>
                      <p className="text-sm text-[#65676B]">Verify charging and earn rewards</p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Favorites */}
          <button
            onClick={() => setShowFavoritesList(true)}
            className="w-full p-4 bg-gray-50 rounded-2xl flex items-center gap-3 hover:bg-gray-100 active:bg-gray-200 transition-colors border border-[#E4E6EB]"
          >
            <div className="w-10 h-10 bg-red-50 rounded-full flex items-center justify-center">
              <Heart className="w-5 h-5 text-red-500" />
            </div>
            <div className="flex-1 text-left">
              <p className="font-medium">Favorites</p>
              <p className="text-sm text-[#65676B]">{favorites.size} saved</p>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </button>

          {/* Share Nerava */}
          <button
            onClick={() => setShowShareNerava(true)}
            className="w-full p-4 bg-blue-50 rounded-2xl flex items-center gap-3 hover:bg-blue-100 active:bg-blue-200 transition-colors border border-blue-100"
          >
            <div className="w-10 h-10 bg-[#1877F2]/20 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-[#1877F2]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3 3h6v6H3V3zm2 2v2h2V5H5zm8-2h6v6h-6V3zm2 2v2h2V5h-2zM3 13h6v6H3v-6zm2 2v2h2v-2H5zm8-2h2v2h-2v-2zm2 0h2v2h-2v-2zm2 0h2v2h-2v-2zm-4 4h2v2h-2v-2zm2 0h2v2h-2v-2zm2 0h2v2h-2v-2zm-4 2h2v2h-2v-2zm2 0h2v2h-2v-2zm2 0h2v2h-2v-2z"/>
              </svg>
            </div>
            <div className="flex-1 text-left">
              <p className="font-medium text-[#1877F2]">Share Nerava</p>
              <p className="text-sm text-[#1877F2]/70">Earn rewards for referrals</p>
            </div>
            <ChevronRight className="w-5 h-5 text-[#1877F2]" />
          </button>

          {/* Preferences */}
          <div className="bg-gray-50 rounded-2xl border border-[#E4E6EB] overflow-hidden">
            <div className="p-4 border-b border-[#E4E6EB]">
              <h3 className="font-semibold text-sm text-[#65676B] uppercase tracking-wide">Preferences</h3>
            </div>
            {/* Notifications toggle */}
            <div className="flex items-center justify-between p-4 border-b border-[#E4E6EB]">
              <div className="flex items-center gap-3">
                {notificationsEnabled ? (
                  <Bell className="w-5 h-5 text-[#65676B]" />
                ) : (
                  <BellOff className="w-5 h-5 text-[#65676B]" />
                )}
                <div>
                  <p className="font-medium text-[#050505]">Notifications</p>
                  <p className="text-sm text-[#65676B]">Charging alerts and offers</p>
                </div>
              </div>
              <button
                onClick={handleToggleNotifications}
                className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors ${
                  notificationsEnabled ? 'bg-[#1877F2]' : 'bg-gray-300'
                }`}
                role="switch"
                aria-checked={notificationsEnabled}
                aria-label="Toggle notifications"
              >
                <span
                  className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform ${
                    notificationsEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            {/* Distance unit toggle */}
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <Ruler className="w-5 h-5 text-[#65676B]" />
                <div>
                  <p className="font-medium text-[#050505]">Distance Unit</p>
                  <p className="text-sm text-[#65676B]">
                    {distanceUnit === 'miles' ? 'Miles' : 'Kilometers'}
                  </p>
                </div>
              </div>
              <button
                onClick={handleToggleDistanceUnit}
                className="px-3 py-1.5 bg-white border border-[#E4E6EB] rounded-full text-sm font-medium text-[#050505] hover:bg-gray-100 active:bg-gray-200 transition-colors"
              >
                {distanceUnit === 'miles' ? 'mi' : 'km'}
              </button>
            </div>
          </div>

          {/* Support */}
          <a
            href="https://nerava.network/support"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full p-4 bg-gray-50 rounded-2xl flex items-center gap-3 hover:bg-gray-100 active:bg-gray-200 transition-colors border border-[#E4E6EB]"
          >
            <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
              <HelpCircle className="w-5 h-5 text-[#65676B]" />
            </div>
            <div className="flex-1 text-left">
              <p className="font-medium">Help & Support</p>
              <p className="text-sm text-[#65676B]">FAQ, contact, and feedback</p>
            </div>
            <ExternalLink className="w-4 h-4 text-gray-400" />
          </a>

          {/* Logout - only show when authenticated */}
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="w-full p-4 bg-red-50 rounded-2xl flex items-center gap-3 hover:bg-red-100 active:bg-red-200 transition-colors border border-red-100"
            >
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <LogOut className="w-5 h-5 text-red-600" />
              </div>
              <span className="text-red-600 font-medium">Log out</span>
            </button>
          )}
        </div>
      )}
    </div>
    </>
  )
}
