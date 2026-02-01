export default function Divider({ className = '' }: { className?: string }) {
  return <hr className={`border-t border-surface opacity-50 my-4 ${className}`} />
}
