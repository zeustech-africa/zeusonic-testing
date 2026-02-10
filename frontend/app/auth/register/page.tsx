"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Container from '../../../components/ui/Container'
import Card from '../../../components/ui/Card'
import Heading from '../../../components/ui/Heading'
import Input from '../../../components/ui/Input'
import Button from '../../../components/ui/Button'
import Link from 'next/link'
import { config } from '../../../lib/config'

export default function RegisterPage() {
  const router = useRouter()
  const isDev = config.authMode === 'DEV'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const res = await fetch(`${config.apiUrl}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data?.detail || 'Unable to register')
      }

      if (typeof window !== 'undefined') {
        localStorage.setItem('zeusonic.pendingVerificationEmail', email)
        localStorage.removeItem('zeusonic.verifiedEmail')
      }
      setSubmitted(true)
      if (isDev) {
        router.push(`/auth/login?email=${encodeURIComponent(email)}`)
      } else {
        router.push(`/auth/verify?email=${encodeURIComponent(email)}`)
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container>
      <div className="max-w-md mx-auto">
        <Card>
          <div className="mb-4">
            <Heading level={2}>Create your account</Heading>
            <p className="text-muted text-sm">
              {isDev ? 'Account created instantly (dev mode).' : 'Join Zeusonic and verify your email to continue.'}
            </p>
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
                placeholder="Minimum 8 characters"
                required
                disabled={loading || submitted}
              />
            </div>
            {error && <div className="text-rose-400 text-sm">{error}</div>}
            <Button type="submit" variant="primary" className="w-full" disabled={loading}>
              {loading ? 'Creating...' : 'Create account'}
            </Button>
          </form>
          <div className="mt-4 text-sm text-muted">
            Already have an account? <Link href="/auth/login" className="text-white">Sign in</Link>
          </div>
        </Card>
      </div>
    </Container>
  )
}
