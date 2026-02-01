import React from 'react'

export default function EmptyState({ title, body }: { title: string; body?: string }) {
  return (
    <div role="status" aria-live="polite" className="rounded p-6 bg-[linear-gradient(180deg,rgba(255,255,255,0.01),transparent)] text-center">
      <div className="text-muted mb-2 font-semibold">{title}</div>
      {body && <div className="text-sm text-muted">{body}</div>}
    </div>
  )
}
