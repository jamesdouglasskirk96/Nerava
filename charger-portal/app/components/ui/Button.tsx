interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'outline'
  onClick?: () => void
  className?: string
  type?: 'button' | 'submit'
  disabled?: boolean
}

export function PrimaryButton({
  children,
  onClick,
  className = '',
  type = 'button',
  disabled = false,
}: Omit<ButtonProps, 'variant'>) {
  const baseClasses =
    'px-6 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
  
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${className}`}
    >
      {children}
    </button>
  )
}

export function SecondaryButton({
  children,
  onClick,
  className = '',
  type = 'button',
  disabled = false,
}: Omit<ButtonProps, 'variant'>) {
  const baseClasses =
    'px-6 py-3 bg-white text-primary border-2 border-primary rounded-lg font-semibold hover:bg-primary-soft transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
  
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${className}`}
    >
      {children}
    </button>
  )
}

export function OutlineButton({
  children,
  onClick,
  className = '',
  type = 'button',
  disabled = false,
}: Omit<ButtonProps, 'variant'>) {
  const baseClasses =
    'px-6 py-3 bg-transparent text-primary border-2 border-primary rounded-lg font-semibold hover:bg-primary-soft transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
  
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${className}`}
    >
      {children}
    </button>
  )
}

