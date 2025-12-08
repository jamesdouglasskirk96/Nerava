interface SectionHeaderProps {
  eyebrow?: string
  title: string
  subtitle?: string
  className?: string
}

export default function SectionHeader({ 
  eyebrow, 
  title, 
  subtitle,
  className = '' 
}: SectionHeaderProps) {
  return (
    <div className={`text-center mb-12 ${className}`}>
      {eyebrow && (
        <p className="text-sm font-semibold text-primary uppercase tracking-wider mb-2">
          {eyebrow}
        </p>
      )}
      <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4">
        {title}
      </h2>
      {subtitle && (
        <p className="text-lg text-gray-600 max-w-3xl mx-auto">
          {subtitle}
        </p>
      )}
    </div>
  )
}

