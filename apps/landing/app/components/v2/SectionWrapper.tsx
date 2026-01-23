interface SectionWrapperProps {
  children: React.ReactNode
  className?: string
  id?: string
}

export default function SectionWrapper({ 
  children, 
  className = '', 
  id 
}: SectionWrapperProps) {
  return (
    <section 
      id={id}
      className={`max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 lg:py-20 ${className}`}
    >
      {children}
    </section>
  )
}

