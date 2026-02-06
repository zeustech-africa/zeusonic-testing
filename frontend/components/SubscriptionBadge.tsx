"use client"

import React, { useEffect, useState } from 'react'
import { config } from '../lib/config'

type SubInfo = {
  plan_code: string | null
  plan_name?: string | null
  status?: string
  entitlements?: Record<string, any>
}

function SubscriptionBadgeInner() {
  const [info, setInfo] = useState<SubInfo | null>(null)

  useEffect(() => {
    let mounted = true
    const key = typeof window !== 'undefined' ? window.localStorage.getItem('ZEUSONIC_API_KEY') : null
    if (!key) return

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 5000)

    fetch(`${config.apiUrl}/api/v1/subscription`, { headers: { 'X-API-Key': key }, signal: controller.signal })
      .then((r) => r.json())
      .then((d) => {
        if (!mounted) return
        if (process.env.NODE_ENV === 'development') console.info('[subscription] fetched', d.plan_code || d.tier)
        setInfo(d)
      })
      .catch(() => setInfo(null))
      .finally(() => clearTimeout(timeout))

    return () => { mounted = false; controller.abort(); clearTimeout(timeout) }
  }, [])

  if (!info) return <div className="text-muted">Tier: —</div>

  const plan = info.plan_code || info.tier || 'FREE'
  const status = info.status || 'fallback'
  const className = plan === 'PRO' ? 'tier-pro' : plan === 'CREATOR' ? 'tier-creator' : 'tier-free'

  return (
    <div className={`inline-flex items-center gap-2 ${className}`} title={info.plan_name ? `${info.plan_name} — ${status}` : `Tier: ${plan}`} role="status" aria-live="polite">
      <div className="badge-inner px-3 py-1 rounded-full text-sm font-semibold border border-white/6" aria-label={`Subscription plan ${plan}`}>
        {plan}
      </div>
    </div>
  )
}

export default React.memo(SubscriptionBadgeInner)
