"use client"

import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

const TOKEN_KEY = 'zeusonic_auth_token'
const EMAIL_KEY = 'zeusonic_auth_email'
const TIER_KEY = 'zeusonic_auth_tier'

export type AuthUser = {
  email: string
}

type AuthContextValue = {
  user: AuthUser | null
  token: string | null
  tier: string
  isAuthenticated: boolean
  isReady: boolean
  login: (token: string) => void
  logout: () => void
  setTier: (tier: string) => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function decodeJwt(token: string): { sub?: string; exp?: number } | null {
  try {
    const parts = token.split('.')
    if (parts.length < 2) return null
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const json = JSON.parse(atob(payload))
    return json
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<AuthUser | null>(null)
  const [tier, setTierState] = useState<string>('FREE')
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    const storedToken = typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null
    const storedEmail = typeof window !== 'undefined' ? localStorage.getItem(EMAIL_KEY) : null
    const storedTier = typeof window !== 'undefined' ? localStorage.getItem(TIER_KEY) : null

    if (storedTier) setTierState(storedTier)

    if (storedToken) {
      const payload = decodeJwt(storedToken)
      const now = Math.floor(Date.now() / 1000)
      if (payload?.exp && payload.exp < now) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(EMAIL_KEY)
      } else {
        setToken(storedToken)
        const email = payload?.sub || storedEmail
        if (email) setUser({ email })
      }
    }

    setIsReady(true)
  }, [])

  useEffect(() => {
    if (!token) return

    fetch('/api/v1/billing/status', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : Promise.reject(r))
      .then((data) => {
        const nextTier = data?.plan_code || data?.tier || 'FREE'
        setTierState(nextTier)
        localStorage.setItem(TIER_KEY, nextTier)
      })
      .catch(() => {})
  }, [token])

  const login = (newToken: string) => {
    const payload = decodeJwt(newToken)
    const email = payload?.sub
    setToken(newToken)
    if (email) {
      setUser({ email })
      localStorage.setItem(EMAIL_KEY, email)
    }
    localStorage.setItem(TOKEN_KEY, newToken)
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(EMAIL_KEY)
  }

  const setTier = (nextTier: string) => {
    setTierState(nextTier)
    localStorage.setItem(TIER_KEY, nextTier)
  }

  const value = useMemo<AuthContextValue>(() => ({
    user,
    token,
    tier,
    isAuthenticated: Boolean(token),
    isReady,
    login,
    logout,
    setTier,
  }), [user, token, tier, isReady])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
