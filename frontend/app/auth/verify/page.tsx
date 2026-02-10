"use client"

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Container from '../../../components/ui/Container'
import Card from '../../../components/ui/Card'
import Heading from '../../../components/ui/Heading'
import Input from '../../../components/ui/Input'
import Button from '../../../components/ui/Button'
import Link from 'next/link'
import { config } from '../../../lib/config'

export default function VerifyPage() {
  const router = useRouter()
  const params = useSearchParams()
  const initialEmail = params.get('email') || ''
  const isDev = config.authMode === 'DEV'

  const [email, setEmail] = useState(initialEmail)
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (isDev) {
    return (
      <Container>
        <div className="max-w-md mx-auto">
          <Card>
            <div className="mb-4">
              <Heading level={2}>OTP disabled</Heading>
              <p className="text-muted text-sm">OTP verification is disabled in dev mode.</p>
            </div>
            <Button type="button" variant="primary" className="w-full" onClick={() => router.push(`/auth/login?email=${encodeURIComponent(initialEmail)}`)}>
              Continue to login
            </Button>
          </Card>
        </div>
      </Container>
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const res = await fetch(`${config.apiUrl}/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp: code }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data?.detail || 'Verification failed')
      }

      if (typeof window !== 'undefined') {
        localStorage.setItem('zeusonic.verifiedEmail', email)
        const pendingEmail = localStorage.getItem('zeusonic.pendingVerificationEmail')
        if (pendingEmail === email) {
          localStorage.removeItem('zeusonic.pendingVerificationEmail')
        }
      }

      router.push(`/auth/login?email=${encodeURIComponent(email)}`)
    } catch (err: any) {
      setError(err.message || 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container>
      <div className="max-w-md mx-auto">
        <Card>
          <div className="mb-4">
            <Heading level={2}>Verify your email</Heading>
            <p className="text-muted text-sm">Enter the 6-digit code sent to your email.</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm text-muted">Email</label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@domain.com" required />
            </div>
            <div>
              <label className="text-sm text-muted">Verification code</label>
              <Input type="text" value={code} onChange={(e) => setCode(e.target.value)} placeholder="6-digit code" required maxLength={6} />
            </div>
            {error && <div className="text-rose-400 text-sm">{error}</div>}
            <Button type="submit" variant="primary" className="w-full" disabled={loading}>
              {loading ? 'Verifying...' : 'Verify'}
            </Button>
          </form>
          <div className="mt-4 text-sm text-muted">
            Need an account? <Link href="/auth/register" className="text-white">Create one</Link>
          </div>
        </Card>
      </div>
    </Container>
  )
}
