export default function Badge({ children, variant = 'accent', className = '' }: { children: React.ReactNode; variant?: 'accent' | 'muted'; className?: string }) {
  const base = 'inline-flex items-center gap-2 px-2 py-0.5 rounded-full text-xs font-semibold'
  const variantClass = variant === 'accent' ? 'bg-accent text-white' : 'bg-surface text-muted border border-white/6'
  return <span className={`${base} ${variantClass} ${className}`}>{children}</span>
}
