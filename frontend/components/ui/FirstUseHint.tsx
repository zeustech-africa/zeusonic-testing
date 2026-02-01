"use client"

import React, { useEffect, useState } from 'react'

type Props = {
  storageKey: string
  message: string
  className?: string
}

export default function FirstUseHint({ storageKey, message, className = '' }: Props) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    try {
      const seen = typeof window !== 'undefined' ? window.localStorage.getItem(storageKey) : null
      if (!seen) setVisible(true)
    } catch (e) {
      // ignore storage errors
      setVisible(false)
    }
  }, [storageKey])

  if (!visible) return null

  return (
    <div className={`first-use-hint ${className}`} role="note" aria-live="polite">
      <div className="first-use-text">{message}</div>
      <button className="first-use-dismiss" onClick={() => { try { window.localStorage.setItem(storageKey, 'true') } catch (e) {} setVisible(false) }} aria-label="Dismiss hint">Got it</button>
    </div>
  )
}
