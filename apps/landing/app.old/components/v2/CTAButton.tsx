import { PrimaryButton, SecondaryButton, OutlineButton } from '../Button'

interface CTAButtonProps {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'outline'
  href?: string
  onClick?: () => void
  className?: string
}

export default function CTAButton({ 
  variant = 'primary',
  ...props 
}: CTAButtonProps) {
  if (variant === 'secondary') {
    return <SecondaryButton {...props} />
  }
  if (variant === 'outline') {
    return <OutlineButton {...props} />
  }
  return <PrimaryButton {...props} />
}

