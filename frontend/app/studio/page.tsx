"use client"

import { useState, useEffect } from 'react'
import RequireAuth from '../../components/auth/RequireAuth'
import { useAuth } from '../../components/auth/AuthProvider'
import StudioInterface from '../../components/StudioInterface'

export default function StudioPage() {
  const { token, apiKey } = useAuth()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => setLoading(false), 500)
    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <RequireAuth>
        <div className="w-screen h-screen bg-black flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-4 border-gray-700 border-t-purple-500 animate-spin mx-auto mb-4"></div>
            <p className="text-gray-400">Loading Studio...</p>
          </div>
        </div>
      </RequireAuth>
    )
  }

  return (
    <RequireAuth>
      <StudioInterface apiKey={apiKey || ''} />
    </RequireAuth>
  )
}
