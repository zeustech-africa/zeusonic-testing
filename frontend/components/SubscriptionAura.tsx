"use client"

import React, { useEffect } from 'react'
import { config } from '../lib/config'
import { useAuth } from './auth/AuthProvider'

function SubscriptionAuraInner({ targetId = 'center-canvas' }: { targetId?: string }) {
  const { token } = useAuth()
  useEffect(() => {
    let mounted = true
    if (!token) return

    fetch(`${config.apiUrl}/api/v1/billing/status`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((d) => {
        if (!mounted) return
        const plan = d.plan_code || d.tier || 'FREE'
        if (process.env.NODE_ENV === 'development') console.info('[subscription] aura apply', plan)
        const el = document.getElementById(targetId)
        if (!el) return
        // minimize DOM writes: compute and set only necessary classes
        const classes = ['tier-free', 'tier-creator', 'tier-pro']
        classes.forEach(c => el.classList.remove(c))
        const cls = plan === 'PRO' ? 'tier-pro' : plan === 'CREATOR' ? 'tier-creator' : 'tier-free'
        el.classList.add(cls)
      })
      .catch(() => {})

    return () => { mounted = false }
  }, [targetId, token])

  return null
}

export default React.memo(SubscriptionAuraInner)
