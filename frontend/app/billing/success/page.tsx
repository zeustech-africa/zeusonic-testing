"use client"

import { useEffect, useState } from 'react'
import AppLayout from '../../../components/AppLayout'
import RequireAuth from '../../../components/auth/RequireAuth'
import { useAuth } from '../../../components/auth/AuthProvider'

export default function BillingSuccessPage() {
  const { token, setTier } = useAuth()
  const [message, setMessage] = useState('Finalizing your subscription...')

  useEffect(() => {
    if (!token) return

    fetch('/api/v1/billing/status', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : Promise.reject(r))
      .then((data) => {
        const nextTier = data?.plan_code || data?.tier || 'FREE'
        setTier(nextTier)
        setMessage('Subscription active. Your account has been upgraded.')
      })
      .catch(() => {
        setMessage('Payment received. Your account will update shortly.')
      })
  }, [token, setTier])

  return (
    <RequireAuth>
      <AppLayout title="Billing">
        <div className="p-6">
          <div className="bg-black/30 border border-purple-500/20 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-white">Success</h2>
            <p className="text-gray-400 mt-2">{message}</p>
            <a
              href="/dashboard"
              className="inline-block mt-6 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              Go to Dashboard
            </a>
          </div>
        </div>
      </AppLayout>
    </RequireAuth>
  )
}
