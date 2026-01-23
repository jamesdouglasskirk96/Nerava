// Button component using design tokens
// Tokens are defined in tailwind.config.js and match src/ui/tokens.ts
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary'
  children: React.ReactNode
}

export function Button({ variant = 'primary', children, className = '', ...props }: ButtonProps) {
  // Using Tailwind classes that match tokens from tailwind.config.js
  // Tokens: padding (px-4 = 16px = spacing.lg, py-3 = 12px = spacing.md)
  // borderRadius: rounded-lg = 8px = borderRadius.button
  // Colors: facebook-blue = #1877F2, gray-900, gray-300 from tokens
  const baseClasses = 'px-4 py-3 rounded-lg font-semibold text-base transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]'
  const variantClasses = {
    primary: 'bg-facebook-blue text-white hover:bg-[#166FE5] shadow-sm',
    secondary: 'bg-white text-gray-900 border border-gray-300 hover:bg-gray-50',
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

