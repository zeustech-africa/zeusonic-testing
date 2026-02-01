"use client"

import React, { useEffect, useState } from 'react'
import BetaBadge from './BetaBadge'

export default function BetaArea() {
  const [betaMode, setBetaMode] = useState<boolean | undefined>(undefined)

  useEffect(() => {
    let mounted = true
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 4000)

    fetch('/api/v1/meta', { signal: controller.signal })
      .then((r) => r.json())
      .then((d) => {
        if (!mounted) return
        setBetaMode(Boolean(d.beta_mode))
      })
      .catch(() => { if (mounted) setBetaMode(false) })
      .finally(() => clearTimeout(timeout))

    return () => { mounted = false; controller.abort(); clearTimeout(timeout) }
  }, [])

  return (
    <div className="beta-reserve" aria-hidden={betaMode !== true}>
      {betaMode === true ? <BetaBadge /> : <span className="beta-placeholder" />}
    </div>
  )
}
