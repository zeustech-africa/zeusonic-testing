"use client"

import React, { useEffect, useState } from 'react'
import { config } from '../lib/config'

export default function BetaSupport() {
  const [betaMode, setBetaMode] = useState<boolean | undefined>(undefined)

  useEffect(() => {
    let mounted = true
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3500)

    fetch(`${config.apiUrl}/api/v1/meta`, { signal: controller.signal })
      .then((r) => r.json())
      .then((d) => { if (!mounted) return; setBetaMode(Boolean(d.beta_mode)) })
      .catch(() => { if (mounted) setBetaMode(false) })
      .finally(() => clearTimeout(timeout))

    return () => { mounted = false; controller.abort(); clearTimeout(timeout) }
  }, [])

  if (!betaMode) return null

  return (
    <div className="beta-support">
      <a className="text-muted text-sm" href="mailto:beta@zeusonic.example?subject=Zeusonic%20Beta%20Feedback" aria-label="Report issue via email">Report issue</a>
      <span className="mx-2">·</span>
      <a className="text-muted text-sm" href="mailto:feedback@zeusonic.example?subject=Zeusonic%20Feedback" aria-label="Send feedback via email">Send feedback</a>
    </div>
  )
}
