// Charging state pill matching Figma exactly
interface ChargingActivePillProps {
  onClick?: () => void
  isCharging?: boolean // true = "Charging Now", false = "Find A Charger"
}

export function ChargingActivePill({ onClick, isCharging = true }: ChargingActivePillProps) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1.5 bg-[#1877F2] rounded-full hover:bg-[#166FE5] active:scale-95 transition-all flex items-center justify-center"
    >
      <span className="text-xs text-white font-medium leading-none">
        {isCharging ? "Charging Now" : "Find A Charger"}
      </span>
    </button>
  )
}

