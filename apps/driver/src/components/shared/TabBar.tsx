import { MapPin, Wallet, User } from 'lucide-react'

export type TabId = 'stations' | 'wallet' | 'account'

interface TabBarProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  walletBalance?: number
  showTeslaPrompt?: boolean
}

const tabs: { id: TabId; label: string; Icon: typeof MapPin }[] = [
  { id: 'stations', label: 'Stations', Icon: MapPin },
  { id: 'wallet', label: 'Wallet', Icon: Wallet },
  { id: 'account', label: 'Account', Icon: User },
]

export function TabBar({ activeTab, onTabChange, walletBalance, showTeslaPrompt }: TabBarProps) {
  return (
    <nav className="flex-shrink-0 bg-white border-t border-gray-200 pb-[env(safe-area-inset-bottom)]">
      <div className="flex items-center justify-around px-4 pt-2 pb-1">
        {tabs.map(({ id, label, Icon }) => {
          const isActive = activeTab === id
          return (
            <button
              key={id}
              onClick={() => onTabChange(id)}
              className="flex flex-col items-center gap-0.5 py-1 px-4 min-w-[64px] relative"
            >
              <div className="relative">
                <Icon
                  className={`w-5 h-5 transition-colors ${
                    isActive ? 'text-[#1877F2]' : 'text-gray-500'
                  }`}
                />
                {/* Wallet balance badge */}
                {id === 'wallet' && walletBalance != null && walletBalance > 0 && (
                  <span className="absolute -top-1.5 -right-3 bg-[#1877F2] text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center leading-none">
                    ${(walletBalance / 100).toFixed(0)}
                  </span>
                )}
                {/* Tesla connect prompt dot */}
                {id === 'account' && showTeslaPrompt && (
                  <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-orange-500 rounded-full" />
                )}
              </div>
              <span
                className={`text-[10px] font-medium transition-colors ${
                  isActive ? 'text-[#1877F2]' : 'text-gray-500'
                }`}
              >
                {label}
              </span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
