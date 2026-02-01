export default function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-surface rounded ${'shadow-soft'} p-4 ${className}`}>
      {children}
    </div>
  )
}
