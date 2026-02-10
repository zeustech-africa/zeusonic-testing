"use client"

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Container from '../../../components/ui/Container'
import Card from '../../../components/ui/Card'
import Heading from '../../../components/ui/Heading'
import Input from '../../../components/ui/Input'
import Button from '../../../components/ui/Button'
import Link from 'next/link'
import { useAuth } from '../../../components/auth/AuthProvider'
import { config } from '../../../lib/config'

export default function LoginPage() {
  const router = useRouter()
  const params = useSearchParams()
  const next = params.get('next') || '/dashboard'
  const emailParam = params.get('email') || ''
  const { login } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [pendingEmail, setPendingEmail] = useState<string | null>(null)
  const [verifiedEmail, setVerifiedEmail] = useState<string | null>(null)

  useEffect(() => {
    if (emailParam && !email) {
      setEmail(emailParam)
    }
  }, [emailParam, email])

  useEffect(() => {
    if (typeof window === 'undefined') return
    setPendingEmail(localStorage.getItem('zeusonic.pendingVerificationEmail'))
    setVerifiedEmail(localStorage.getItem('zeusonic.verifiedEmail'))
  }, [email])

  const isPendingVerification = !!email && pendingEmail === email && verifiedEmail !== email

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (isPendingVerification) {
      setError('Please verify your email before logging in.')
      return
    }

    setLoading(true)

    try {
      const loginUrl = `${config.apiUrl}/auth/login`
      console.info('[AUTH][LOGIN] Request URL:', loginUrl)

      const res = await fetch(loginUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        console.warn('[AUTH][LOGIN] Non-OK response:', res.status, data)
        if (res.status === 401) {
          throw new Error('Invalid credentials — this usually means the password doesn’t match the one you registered with.')
        }
        throw new Error(data?.detail || 'Invalid credentials')
      }

      const data = await res.json()
      if (!data?.access_token) throw new Error('Missing access token')

      login(data.access_token)
      router.push(next)
    } catch (err: any) {
      console.error('[AUTH][LOGIN] Request failed:', err)
      setError(err?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container>
      <div className="max-w-md mx-auto">
        <Card>
          <div className="mb-4">
            <Heading level={2}>Sign in</Heading>
            <p className="text-muted text-sm">Access your Zeusonic workspace.</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm text-muted">Email</label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@domain.com" required />
            </div>
            <div>
              <label className="text-sm text-muted">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your password"
                required
                disabled={loading || isPendingVerification}
                autoComplete="new-password"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck={false}
                inputMode="text"
                name="password-no-autofill"
                data-lpignore="true"
              />
              <p className="text-xs text-muted mt-1">Use the SAME password you registered with.</p>
            </div>
            {isPendingVerification && (
              <div className="text-amber-400 text-sm">Please verify your email before logging in.</div>
            )}
            {error && <div className="text-rose-400 text-sm">{error}</div>}
            <Button type="submit" variant="primary" className="w-full" disabled={loading || isPendingVerification}>
              {loading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>
          <div className="mt-4 text-sm text-muted">
            New here? <Link href="/auth/register" className="text-white">Create an account</Link>
          </div>
        </Card>
      </div>
    </Container>
  )
}
