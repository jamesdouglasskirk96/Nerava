// Button component using design tokens
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary'
  children: React.ReactNode
}

export function Button({ variant = 'primary', children, className = '', ...props }: ButtonProps) {
  const baseClasses = 'px-4 py-3 rounded-lg font-semibold text-base transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]'
  const variantClasses = {
    primary: 'bg-[#1877F2] text-white hover:bg-[#166FE5] shadow-sm',
    secondary: 'bg-white text-[#050505] border border-[#E4E6EB] hover:bg-gray-50',
  }

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

