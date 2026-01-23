import Link from 'next/link'

interface ButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'outline'
  href?: string
  onClick?: () => void
  className?: string
  type?: 'button' | 'submit'
}

export function PrimaryButton({ 
  children, 
  href, 
  onClick, 
  className = '' 
}: Omit<ButtonProps, 'variant'>) {
  const baseClasses = 'px-6 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-primary-dark transition-colors inline-block text-center'
  
  if (href) {
    return (
      <Link href={href} className={`${baseClasses} ${className}`}>
        {children}
      </Link>
    )
  }
  
  return (
    <button onClick={onClick} className={`${baseClasses} ${className}`}>
      {children}
    </button>
  )
}

export function SecondaryButton({ 
  children, 
  href, 
  onClick, 
  className = '' 
}: Omit<ButtonProps, 'variant'>) {
  const baseClasses = 'px-6 py-3 bg-white text-primary border-2 border-primary rounded-lg font-semibold hover:bg-primary-soft transition-colors inline-block text-center'
  
  if (href) {
    return (
      <Link href={href} className={`${baseClasses} ${className}`}>
        {children}
      </Link>
    )
  }
  
  return (
    <button onClick={onClick} className={`${baseClasses} ${className}`}>
      {children}
    </button>
  )
}

export function OutlineButton({ 
  children, 
  href, 
  onClick, 
  className = '' 
}: Omit<ButtonProps, 'variant'>) {
  const baseClasses = 'px-6 py-3 bg-transparent text-primary border-2 border-primary rounded-lg font-semibold hover:bg-primary-soft transition-colors inline-block text-center'
  
  if (href) {
    return (
      <Link href={href} className={`${baseClasses} ${className}`}>
        {children}
      </Link>
    )
  }
  
  return (
    <button onClick={onClick} className={`${baseClasses} ${className}`}>
      {children}
    </button>
  )
}

