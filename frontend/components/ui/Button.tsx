type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost' | 'upgrade'
  size?: 'sm' | 'md' | 'lg'
}

export default function Button({ variant = 'primary', size = 'md', className = '', children, disabled = false, ...rest }: ButtonProps) {
  const base = 'btn font-medium'
  const sizeClass = size === 'sm' ? 'px-3 py-2 text-sm' : size === 'lg' ? 'px-5 py-3 text-base' : 'px-4 py-2 text-sm'

  const variantClass = variant === 'primary' ? 'btn-primary' : variant === 'secondary' ? 'btn-secondary' : variant === 'upgrade' ? 'btn-upgrade' : 'bg-transparent text-muted border border-white/6'

  const disabledClass = disabled ? 'btn-disabled' : 'hover:opacity-95 focus-visible:outline-none'

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    // Ensure Space/Enter trigger on custom buttons consistently
    if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
      // allow native behavior
    }
  }

  return (
    <button className={`${base} ${sizeClass} ${variantClass} ${disabledClass} ${className}`} disabled={disabled} aria-disabled={disabled} onKeyDown={handleKeyDown} {...rest}>
      {children}
    </button>
  )
}
