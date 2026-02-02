"use client"

import { useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from './AuthProvider'

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isReady } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!isReady) return
    if (!isAuthenticated) {
      const next = pathname ? `?next=${encodeURIComponent(pathname)}` : ''
      router.replace(`/auth/login${next}`)
    }
  }, [isAuthenticated, isReady, pathname, router])

  if (!isReady) return null
  if (!isAuthenticated) return null

  return <>{children}</>
}
