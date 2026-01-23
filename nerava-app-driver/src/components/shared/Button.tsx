// Button component using design tokens
// Tokens are defined in tailwind.config.js and match src/ui/tokens.ts
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary'
  children: React.ReactNode
}

export function Button({ variant = 'primary', children, className = '', disabled, ...props }: ButtonProps) {
  // Using Tailwind classes that match Figma design exactly
  const baseClasses = 'w-full py-3.5 rounded-2xl font-medium transition-all active:scale-98'
  const variantClasses = {
    primary: disabled 
      ? 'bg-[#E4E6EB] text-[#65676B] cursor-not-allowed'
      : 'bg-[#1877F2] text-white hover:bg-[#166FE5]',
    secondary: 'bg-white border-2 border-[#1877F2] text-[#1877F2] hover:bg-[#F7F8FA]',
  }

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}

