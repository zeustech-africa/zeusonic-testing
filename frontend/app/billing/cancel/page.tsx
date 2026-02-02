"use client"

import AppLayout from '../../../components/AppLayout'
import RequireAuth from '../../../components/auth/RequireAuth'

export default function BillingCancelPage() {
  return (
    <RequireAuth>
      <AppLayout title="Billing">
        <div className="p-6">
          <div className="bg-black/30 border border-purple-500/20 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-white">Checkout Canceled</h2>
            <p className="text-gray-400 mt-2">No changes were made to your subscription.</p>
            <a
              href="/billing"
              className="inline-block mt-6 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              Back to Billing
            </a>
          </div>
        </div>
      </AppLayout>
    </RequireAuth>
  )
}
