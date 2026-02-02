"use client"

import { useMemo, useState } from 'react'
import AppLayout from '../../components/AppLayout'
import Button from '../../components/ui/Button'
import RequireAuth from '../../components/auth/RequireAuth'
import { useAuth } from '../../components/auth/AuthProvider'

export default function BillingPage() {
  const { token, tier, isReady } = useAuth()
  const [interval, setInterval] = useState<'monthly' | 'yearly'>('monthly')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const priceLabel = useMemo(() => {
    return interval === 'monthly' ? '$19/mo' : '$190/yr'
  }, [interval])

  const handleCheckout = async () => {
    if (!token) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/v1/billing/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ plan: interval }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.detail || 'Checkout failed')
      }
      const data = await res.json()
      if (data?.url) {
        window.location.href = data.url
      } else {
        throw new Error('Missing checkout URL')
      }
    } catch (err: any) {
      setError(err?.message || 'Checkout failed')
    } finally {
      setLoading(false)
    }
  }

  if (!isReady) {
    return (
      <RequireAuth>
        <AppLayout title="Billing">
          <div className="p-6 text-gray-400">Loading...</div>
        </AppLayout>
      </RequireAuth>
    )
  }

  return (
    <RequireAuth>
      <AppLayout title="Billing">
        <div className="p-6 space-y-6">
          <div className="bg-black/30 border border-purple-500/20 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-white">Upgrade to Pro</h2>
            <p className="text-gray-400 mt-2">Unlock unlimited projects and premium processing.</p>

            <div className="mt-6 flex items-center gap-3">
              <button
                className={`px-4 py-2 rounded-full text-sm border ${interval === 'monthly' ? 'bg-purple-600 border-purple-500 text-white' : 'border-white/10 text-gray-300'}`}
                onClick={() => setInterval('monthly')}
              >
                Monthly
              </button>
              <button
                className={`px-4 py-2 rounded-full text-sm border ${interval === 'yearly' ? 'bg-purple-600 border-purple-500 text-white' : 'border-white/10 text-gray-300'}`}
                onClick={() => setInterval('yearly')}
              >
                Yearly
              </button>
            </div>

            <div className="mt-6 flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-white">{priceLabel}</div>
                <div className="text-gray-400 text-sm">Cancel anytime</div>
              </div>
              <Button variant="primary" size="lg" disabled={loading || tier !== 'FREE'} onClick={handleCheckout}>
                {tier === 'FREE' ? (loading ? 'Redirecting...' : 'Upgrade') : 'Current Plan'}
              </Button>
            </div>

            {error && <div className="mt-4 text-red-400 text-sm">{error}</div>}
          </div>
        </div>
      </AppLayout>
    </RequireAuth>
  )
}
