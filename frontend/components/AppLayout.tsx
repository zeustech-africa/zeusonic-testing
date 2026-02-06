"use client"

import { useEffect, useMemo, useState } from 'react'
import Container from './ui/Container'
import Heading from './ui/Heading'
import Card from './ui/Card'
import Divider from './ui/Divider'
import Button from './ui/Button'
import Link from 'next/link'
import SubscriptionBadge from './SubscriptionBadge'
import SubscriptionAura from './SubscriptionAura'
import BetaArea from './BetaArea'
import BetaOnboarding from './BetaOnboarding'
import BetaSupport from './BetaSupport'
import UploadDisabledBanner from './UploadDisabledBanner'
import { useAuth } from './auth/AuthProvider'
import { config } from '../lib/config'

export default function AppLayout({ children, title }: { children: React.ReactNode; title?: string }) {
  const { token, tier, isAuthenticated } = useAuth()
  const [projectCount, setProjectCount] = useState<number | null>(null)
  const [billingStatus, setBillingStatus] = useState<{ tier: string; subscription_status?: string | null; current_period_end?: string | null; entitlements?: Record<string, any> } | null>(null)

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setProjectCount(null)
      return
    }

    let mounted = true
    const controller = new AbortController()

    fetch(`${config.apiUrl}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    })
      .then((r) => r.ok ? r.json() : Promise.reject(r))
      .then((data) => {
        if (!mounted) return
        const count = Array.isArray(data?.projects) ? data.projects.length : 0
        setProjectCount(count)
      })
      .catch(() => { if (mounted) setProjectCount(null) })

    return () => { mounted = false; controller.abort() }
  }, [isAuthenticated, token])

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setBillingStatus(null)
      return
    }

    let mounted = true
    const controller = new AbortController()

    fetch(`${config.apiUrl}/api/v1/billing/status`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    })
      .then((r) => r.ok ? r.json() : Promise.reject(r))
      .then((data) => { if (mounted) setBillingStatus(data) })
      .catch(() => { if (mounted) setBillingStatus(null) })

    return () => { mounted = false; controller.abort() }
  }, [isAuthenticated, token])

  const projectLimit = useMemo(() => {
    if (!isAuthenticated) return null
    return tier === 'FREE' ? 2 : null
  }, [isAuthenticated, tier])

  const limitReached = projectLimit !== null && projectCount !== null && projectCount >= projectLimit

  const billingText = useMemo(() => {
    if (!billingStatus) return null
    const planTier = billingStatus.tier || tier
    if (planTier === 'FREE') return 'Free Plan — 2 projects max'

    const status = billingStatus.subscription_status ? billingStatus.subscription_status.toString() : 'active'
    const periodEnd = billingStatus.current_period_end ? new Date(billingStatus.current_period_end).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : null
    const suffix = periodEnd ? ` (renews ${periodEnd})` : ''
    return `Pro Plan — ${status.charAt(0).toUpperCase() + status.slice(1)}${suffix}`
  }, [billingStatus, tier])

  return (
    <div className="min-h-screen bg-base text-white">
      <div className="border-b border-surface">
        <Container>
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center gap-4">
              <img src="/brand/zeusonic/logo.png" alt="Zeusonic" className="h-10 w-auto" />
<span className="text-muted text-sm hidden sm:inline">by</span>
<img src="/brand/zeustech/logo.png" alt="ZeusTech" className="h-6 w-auto hidden sm:inline opacity-80" />
            </div>
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/dashboard" className="text-muted hover:text-white">Dashboard</Link>
              <Link href="/studio" className="text-muted hover:text-white">Studio</Link>
              <Link href="/generate" className="text-muted hover:text-white">Generate</Link>
              <Link href="/library" className="text-muted hover:text-white">Library</Link>
              <div className="ml-4 flex items-center gap-2">
                <Button variant="secondary" size="sm">Preview</Button>
                <Button variant="primary" size="sm" disabled={Boolean(limitReached)}>
                  New
                </Button>
                {limitReached && (
                  <div className="text-xs text-muted">
                    Free plan limited to 2 projects. <Link href="/billing" className="underline">Upgrade</Link>
                  </div>
                )}
              </div>
              <div className="ml-6 flex items-center gap-2">
                <SubscriptionBadge />
                {billingText && (
                  <div className="text-xs text-muted" aria-live="polite">{billingText}</div>
                )}
                {tier === 'FREE' && (
                  <Link href="/billing" className="inline-flex">
                    <Button variant="primary" size="sm">Upgrade</Button>
                  </Link>
                )}
                <BetaArea />
              </div>
            </nav>
            <div className="md:hidden">
              {/* Mobile compact header actions */}
              <Button variant="ghost" size="sm">Menu</Button>
            </div>
            <BetaOnboarding />
            <UploadDisabledBanner />
          </div>
        </Container>
      </div>

      <main className="py-8">
        <Container>
          {title && <div className="mb-4"><Heading level={1}>{title}</Heading><Divider /></div>}

          <div className="studio-grid">
            <aside className="left-rail" role="navigation" aria-label="Tool rail">
              <div className="flex flex-col gap-3" role="tablist" aria-orientation="vertical">
                <Button variant="ghost" size="sm" aria-pressed={false}>Samples</Button>
                <Button variant="ghost" size="sm" aria-pressed={false}>Instruments</Button>
                <Button variant="ghost" size="sm" aria-pressed={false}>Effects</Button>
                <div className="mt-4">
                  <SubscriptionBadge />
                </div>
              </div>
            </aside>

            <section id="center-canvas" className="center-canvas bg-surface shadow-soft relative">
              <SubscriptionAura />
              {children}
              <div className="absolute inset-0 pointer-events-none" />
            </section>

            <aside className="right-panel bg-surface shadow-soft" aria-label="AI Controls">
              <div className="flex flex-col gap-3">
                <div className="font-semibold">AI Controls</div>
                <div className="text-muted text-sm">Parameters and model controls</div>
              </div>
              <div className="mt-4 text-muted text-sm">
                <BetaSupport />
              </div>
            </aside>
          </div>
        </Container>
      </main>

      {/* Mobile bottom nav + floating action button */}
      <nav className="mobile-bottom-nav" role="navigation" aria-label="Mobile navigation">
        <button className="btn btn-secondary" aria-label="Home" onClick={() => { if (process.env.NODE_ENV === 'development') console.info('[nav] home-click') }}>Home</button>
        <button className="btn btn-secondary" aria-label="Generate" onClick={() => { if (process.env.NODE_ENV === 'development') console.info('[nav] generate-click') }}>Generate</button>
        <button className="btn btn-secondary" aria-label="Library" onClick={() => { if (process.env.NODE_ENV === 'development') console.info('[nav] library-click') }}>Library</button>
      </nav>
      <button className="fab" aria-label="New" onClick={() => { if (!limitReached && process.env.NODE_ENV === 'development') console.info('[action] fab-click') }} aria-haspopup="true" aria-disabled={Boolean(limitReached)} disabled={Boolean(limitReached)}>+</button>
    </div>
  )
}
