"use client"

import React, { useEffect, useState } from 'react'
import { config } from '../lib/config'

export default function BetaOnboarding() {
  const [visible, setVisible] = useState(false)
  const [metaLoaded, setMetaLoaded] = useState(false)

  useEffect(() => {
    let mounted = true
    try {
      const seen = typeof window !== 'undefined' ? window.localStorage.getItem('zeusonic_beta_seen') : null
      if (seen === 'true') {
        setVisible(false)
        setMetaLoaded(true)
        return
      }

      const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 4000)

    fetch(`${config.apiUrl}/api/v1/meta`, { signal: controller.signal })
        .then((r) => r.json())
        .then((d) => {
          if (!mounted) return
          if (d && d.beta_mode === true) {
            setVisible(true)
          }
        })
        .catch(() => {
          // swallow: onboarding is non-blocking
        })
        .finally(() => { if (mounted) setMetaLoaded(true); clearTimeout(timeout) })

    return () => { mounted = false; controller.abort(); clearTimeout(timeout) }
    } catch (err) {
      setMetaLoaded(true)
    }

    return () => { mounted = false }
  }, [])

  if (!visible) return null

  return (
    <div className="beta-onboard" role="dialog" aria-live="polite" aria-label="Beta onboarding">
      <div className="beta-onboard-inner">
        <div className="beta-onboard-text">You’re using Zeusonic Beta. Features may evolve.</div>
        <button className="beta-onboard-dismiss" onClick={() => { window.localStorage.setItem('zeusonic_beta_seen', 'true'); setVisible(false) }} aria-label="Dismiss">Dismiss</button>
      </div>
    </div>
  )
}
