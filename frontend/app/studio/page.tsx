"use client"

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import RequireAuth from '../../components/auth/RequireAuth'
import { useAuth } from '../../components/auth/AuthProvider'
import { config } from '../../lib/config'
import AppLayout from '../../components/AppLayout'
import Heading from '../../components/ui/Heading'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import EmptyState from '../../components/ui/EmptyState'
import AudioProcessor from '../../components/AudioProcessor'

interface Project {
  id: number
  name: string
  metadata?: { description?: string } | null
}

export default function StudioPage() {
  const router = useRouter()
  const params = useSearchParams()
  const projectParam = params.get('project')
  const { token } = useAuth()
  const [loading, setLoading] = useState(true)
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<number | null>(projectParam ? Number(projectParam) : null)
  const [projectDetails, setProjectDetails] = useState<Project | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copyStatus, setCopyStatus] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return

    let mounted = true
    setError(null)

    fetch(`${config.apiUrl}/api/v1/projects`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => (res.ok ? res.json() : Promise.reject(res)))
      .then((data) => {
        if (!mounted) return
        const nextProjects = data.projects || []
        setProjects(nextProjects)
        if (!projectParam && nextProjects.length > 0) {
          setSelectedProject(nextProjects[0].id)
        }
      })
      .catch(() => {
        if (mounted) setError('Failed to load projects')
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [token, projectParam])

  useEffect(() => {
    if (!token || !selectedProject) return

    let mounted = true
    setError(null)

    fetch(`${config.apiUrl}/api/v1/projects/${selectedProject}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => (res.ok ? res.json() : Promise.reject(res)))
      .then((data) => {
        if (mounted) setProjectDetails(data)
      })
      .catch(() => {
        if (mounted) setError('Failed to load project')
      })

    return () => {
      mounted = false
    }
  }, [token, selectedProject])

  const handleCopyLink = async () => {
    if (!selectedProject) return
    const url = `${window.location.origin}/studio?project=${selectedProject}`
    try {
      await navigator.clipboard.writeText(url)
      setCopyStatus('Copied studio link')
    } catch {
      setCopyStatus('Unable to copy link')
    }
    setTimeout(() => setCopyStatus(null), 2000)
  }

  return (
    <RequireAuth>
      <AppLayout title="Studio">
        <div className="space-y-6">
          <Heading level={2}>Studio</Heading>

          {loading && (
            <div className="text-gray-400">Loading studio...</div>
          )}

          {!loading && projects.length === 0 && (
            <EmptyState title="No projects yet" body="Create a project on the Dashboard to start producing." />
          )}

          {!loading && projects.length > 0 && (
            <Card>
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-muted">Current project</div>
                    <div className="text-lg font-semibold text-white">
                      {projectDetails?.name || 'Loading project...'}
                    </div>
                    {projectDetails?.metadata?.description && (
                      <div className="text-xs text-muted">{projectDetails.metadata.description}</div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => router.push('/dashboard')}
                    >
                      Switch project
                    </Button>
                    {selectedProject && (
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={handleCopyLink}
                      >
                        Copy studio link
                      </Button>
                    )}
                  </div>
                </div>

                {copyStatus && (
                  <div className="text-xs text-muted">{copyStatus}</div>
                )}

                <div className="flex flex-wrap gap-2">
                  {projects.map((project) => (
                    <Button
                      key={project.id}
                      type="button"
                      variant={project.id === selectedProject ? 'primary' : 'ghost'}
                      onClick={() => {
                        setSelectedProject(project.id)
                        router.replace(`/studio?project=${project.id}`)
                      }}
                    >
                      {project.name}
                    </Button>
                  ))}
                </div>
              </div>
            </Card>
          )}

          {error && <div className="text-rose-400 text-sm">{error}</div>}

          {selectedProject && (
            <Card>
              <AudioProcessor projectId={selectedProject} projectName={projectDetails?.name} />
            </Card>
          )}
        </div>
      </AppLayout>
    </RequireAuth>
  )
}
