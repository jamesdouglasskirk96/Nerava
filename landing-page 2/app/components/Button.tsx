import Link from 'next/link'

interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'text'
  href?: string
  onClick?: () => void
  className?: string
  type?: 'button' | 'submit'
}

const baseStyles = 'px-6 py-3 rounded-lg transition-all duration-200 font-medium'

const variantStyles = {
  primary: 'bg-primary text-primary-foreground hover:opacity-90',
  secondary: 'bg-white text-foreground border border-border hover:bg-secondary',
  text: 'text-foreground hover:text-muted-foreground underline'
}

export function Button({ 
  children, 
  variant = 'primary', 
  href,
  onClick, 
  className = '' 
}: ButtonProps) {
  const combinedClassName = `${baseStyles} ${variantStyles[variant]} ${className}`
  
  if (href) {
    return (
      <Link href={href} className={combinedClassName}>
        {children}
      </Link>
    )
  }
  
  return (
    <button
      onClick={onClick}
      type={onClick ? 'button' : 'submit'}
      className={combinedClassName}
    >
      {children}
    </button>
  )
}

// Legacy exports for backward compatibility
export function PrimaryButton({ 
  children, 
  href, 
  onClick, 
  className = '' 
}: Omit<ButtonProps, 'variant'>) {
  return (
    <Button href={href} onClick={onClick} variant="primary" className={className}>
      {children}
    </Button>
  )
}

export function SecondaryButton({ 
  children, 
  href, 
  onClick, 
  className = '' 
}: Omit<ButtonProps, 'variant'>) {
  return (
    <Button href={href} onClick={onClick} variant="secondary" className={className}>
      {children}
    </Button>
  )
}

export function OutlineButton({ 
  children, 
  href, 
  onClick, 
  className = '' 
}: Omit<ButtonProps, 'variant'>) {
  return (
    <Button href={href} onClick={onClick} variant="secondary" className={className}>
      {children}
    </Button>
  )
}

