"use client"

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import AppLayout from '../../components/AppLayout'
import Heading from '../../components/ui/Heading'
import Card from '../../components/ui/Card'
import AudioUploadPanel from '../../components/features/AudioUploadPanel'
import Timeline from '../../components/Timeline'
import EmptyState from '../../components/ui/EmptyState'
import RequireAuth from '../../components/auth/RequireAuth'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import { useAuth } from '../../components/auth/AuthProvider'
import { config } from '../../lib/config'

type Project = {
  id: number
  name: string
  metadata?: { description?: string } | null
}

export default function DashboardPage() {
  const router = useRouter()
  const { token, logout } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loadingProjects, setLoadingProjects] = useState(true)
  const [projectError, setProjectError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    if (!token) return

    let mounted = true
    const controller = new AbortController()

    setLoadingProjects(true)
    setProjectError(null)

    fetch(`${config.apiUrl}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    })
      .then((r) => {
        if (r.status === 401) {
          logout()
          return Promise.reject(r)
        }
        return r.ok ? r.json() : Promise.reject(r)
      })
      .then((data) => {
        if (!mounted) return
        const nextProjects = Array.isArray(data?.projects) ? data.projects : []
        setProjects(nextProjects)
      })
      .catch(() => {
        if (mounted) setProjectError('Unable to load projects')
      })
      .finally(() => {
        if (mounted) setLoadingProjects(false)
      })

    return () => {
      mounted = false
      controller.abort()
    }
  }, [token, logout])

  const isEmpty = useMemo(() => !loadingProjects && projects.length === 0, [loadingProjects, projects])

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token) return

    setCreating(true)
    setProjectError(null)

    try {
      const res = await fetch(`${config.apiUrl}/api/v1/projects`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          metadata: description ? { description } : undefined,
        }),
      })

      if (res.status === 401) {
        logout()
        return
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data?.detail || 'Failed to create project')
      }

      const created = await res.json()
      setProjects((prev) => [created, ...prev])
      setName('')
      setDescription('')
      setShowCreate(false)
      router.push('/studio')
    } catch (err: any) {
      setProjectError(err?.message || 'Failed to create project')
    } finally {
      setCreating(false)
    }
  }

  return (
    <RequireAuth>
      <AppLayout title="Dashboard">
        <div className="space-y-6">
          <Heading level={2}>Overview</Heading>

          {isEmpty && (
            <Card>
              <div className="space-y-3">
                <div className="text-lg font-semibold">Welcome to Zeusonic</div>
                <p className="text-muted text-sm">Get started by creating your first project.</p>
                <Button type="button" variant="primary" onClick={() => setShowCreate(true)}>
                  Create your first project
                </Button>
              </div>
            </Card>
          )}

          {showCreate && (
            <Card>
              <form onSubmit={handleCreateProject} className="space-y-4">
                <div>
                  <label className="text-sm text-muted">Project name</label>
                  <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="My first project" required />
                </div>
                <div>
                  <label className="text-sm text-muted">Description (optional)</label>
                  <textarea
                    className="w-full rounded-sm px-3 py-2 bg-surface text-white placeholder:text-muted border border-transparent focus:outline-none focus:ring-2 focus:ring-accent"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="What are you creating?"
                    rows={3}
                  />
                </div>
                {projectError && <div className="text-rose-400 text-sm">{projectError}</div>}
                <div className="flex gap-2">
                  <Button type="submit" variant="primary" disabled={creating}>
                    {creating ? 'Creating...' : 'Create project'}
                  </Button>
                  <Button type="button" variant="ghost" onClick={() => setShowCreate(false)} disabled={creating}>
                    Cancel
                  </Button>
                </div>
              </form>
            </Card>
          )}

          {!loadingProjects && projects.length > 0 && (
            <Card>
              <div className="flex items-center justify-between">
                <div className="font-semibold">Your projects</div>
                <Button type="button" variant="secondary" onClick={() => setShowCreate(true)}>
                  New project
                </Button>
              </div>
              <div className="mt-4 space-y-2">
                {projects.map((project) => (
                  <div key={project.id} className="flex items-center justify-between rounded border border-white/5 px-3 py-2">
                    <div>
                      <div className="text-sm font-medium text-white">{project.name}</div>
                      {project.metadata?.description && (
                        <div className="text-xs text-muted">{project.metadata.description}</div>
                      )}
                    </div>
                    <Button type="button" variant="ghost" onClick={() => router.push('/studio')}>
                      Open
                    </Button>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {projectError && !showCreate && (
            <EmptyState title="Unable to load projects" body={projectError} />
          )}

          {/* Presentational Audio upload panel (UI only) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Card>
                <div className="mb-2"><strong>Upload</strong></div>
                <p className="text-muted">Quick access to upload UI (presentational only)</p>
              </Card>
              <div className="mt-4">
                {/* AudioUploadPanel inserted below (live integration enabled) */}
                <AudioUploadPanel live />
                <div className="mt-6">
                  <Timeline />
                </div>
              </div>
            </div>

            <div>
              <Card>
                <div className="mb-2 font-semibold">Processing queue</div>
                <div className="text-muted text-sm">No active jobs yet</div>
                <div className="mt-4"><EmptyState title="No queued jobs" body="Jobs will appear here when processing starts. Start by uploading an audio file." /></div>
              </Card>
            </div>
          </div>
        </div>
      </AppLayout>
    </RequireAuth>
  )
}
