import { InputHTMLAttributes } from 'react'

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  error?: boolean
}

export default function Input({ error = false, className = '', disabled = false, ...rest }: InputProps) {
  const base = 'w-full rounded-sm px-3 py-2 bg-surface text-white placeholder:text-muted border border-transparent focus:outline-none'
  const errorClass = error ? 'border-rose-500' : 'focus:ring-2 focus:ring-accent'
  const disabledClass = disabled ? 'opacity-50 cursor-not-allowed' : ''

  return <input className={`${base} ${errorClass} ${disabledClass} ${className}`} disabled={disabled} {...rest} />
}
