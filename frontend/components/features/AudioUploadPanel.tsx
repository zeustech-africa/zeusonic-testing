"use client"

import React, { useRef, useState, useEffect, useMemo } from 'react'
import EmptyState from '../ui/EmptyState'
import Card from '../ui/Card'
import Heading from '../ui/Heading'
import Button from '../ui/Button'
import FirstUseHint from '../ui/FirstUseHint'
import { config } from '../../lib/config'
import { useAuth } from '../auth/AuthProvider'

type AudioUploadPanelProps = {
  isDragging?: boolean
  hasFile?: boolean
  isUploading?: boolean
  disabled?: boolean
  /** When true the component performs real uploads to the backend */
  live?: boolean
  /** Project id used for JWT-scoped uploads */
  projectId?: number
  /** Optional callback with newly created track id */
  onUploaded?: (trackId: number) => void
}

function AudioUploadPanel({
  isDragging: propIsDragging,
  hasFile: propHasFile,
  isUploading: propIsUploading,
  disabled: propDisabled,
  live = false,
  projectId,
  onUploaded,
}: AudioUploadPanelProps) {
  const { token } = useAuth()
  // internal state when not driven by props
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [disabled, setDisabled] = useState(false)
  const [maintenanceDisabled, setMaintenanceDisabled] = useState<boolean | undefined>(undefined)
  const [statusText, setStatusText] = useState<string | null>(null)
  const [progress, setProgress] = useState<number | null>(null)
  const statusId = useMemo(() => `upload-status-${Math.random().toString(36).slice(2,8)}`, [])
  const inputRef = useRef<HTMLInputElement | null>(null)

  // derive visible states: prefer explicit props when provided
  const isDragging = propIsDragging ?? false
  const hasFile = propHasFile ?? Boolean(file)
  const isUploadingVisible = propIsUploading ?? isUploading
  const disabledVisible = propDisabled ?? disabled

  const dropZoneClass = `border-2 border-dashed rounded p-6 flex flex-col items-center justify-center gap-3 bg-base transition-all duration-150 ${
    isDragging ? 'ring-2' : 'border-surface'
  }`

  const rootClass = ` ${disabledVisible ? 'opacity-50 cursor-not-allowed' : ''}`

  // Fetch server meta to see if uploads are disabled for maintenance
  useEffect(() => {
    let mounted = true
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3000)

    fetch(`${config.apiUrl}/api/v1/meta`, { signal: controller.signal })
      .then((r) => r.json())
      .then((d) => {
        if (!mounted) return
        if (d && d.disable_uploads === true) {
          setMaintenanceDisabled(true)
          setDisabled(true)
          setStatusText('Uploads temporarily paused for maintenance.')
        } else {
          setMaintenanceDisabled(false)
        }
      })
      .catch(() => { if (mounted) setMaintenanceDisabled(false) })
      .finally(() => clearTimeout(timeout))

    return () => { mounted = false; controller.abort(); clearTimeout(timeout) }
  }, [])

  function handleSelectClick() {
    inputRef.current?.click()
  }

  function handleSelectKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      inputRef.current?.click()
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files && e.target.files[0]
    if (f) {
      setFile(f)
      setStatusText(null)
      setProgress(null)
    }
  }

  function uploadLive() {
    if (!file) {
      setStatusText('No file selected')
      return
    }
    if (!projectId) {
      setStatusText('Select a project before uploading.')
      setIsUploading(false)
      setDisabled(false)
      return
    }
    if (!token) {
      setStatusText('Authentication required to upload.')
      setIsUploading(false)
      setDisabled(false)
      return
    }

    const xhr = new XMLHttpRequest()
    const fd = new FormData()
    fd.append('file', file)

    xhr.open('POST', `${config.apiUrl}/api/v1/projects/${projectId}/audio`)
    xhr.setRequestHeader('Authorization', `Bearer ${token}`)

    xhr.upload.onprogress = (ev) => {
      if (ev.lengthComputable) {
        const p = Math.round((ev.loaded / ev.total) * 100)
        setProgress(p)
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText)
          const trackId = data.id
          setStatusText('Upload complete — analysis running in the background.')
          if (typeof trackId === 'number') {
            onUploaded?.(trackId)
          }
        } catch (e) {
          setStatusText('Upload succeeded but response parse failed')
        }
      } else {
        // Try to parse response body for details
        try {
          const body = JSON.parse(xhr.responseText)
          if (body && body.detail) {
            setStatusText(String(body.detail))
          } else {
            setStatusText(`Upload failed (${xhr.status})`)
          }
        } catch (e) {
          setStatusText(`Upload failed (${xhr.status})`)
        }
      }
      // minimal animation/stability: keep small scale while switching to idle
      setTimeout(() => {
        setIsUploading(false)
        setDisabled(false)
      }, 220)
    }

    xhr.onerror = () => {
      setStatusText('Network error during upload')
      setIsUploading(false)
      setDisabled(false)
    }

    // instrumentation: lightweight log (dev only)
    if (process.env.NODE_ENV === 'development') console.info('[upload] attempt', { filename: file.name, projectId })

    setIsUploading(true)
    setDisabled(true)
    setStatusText('Uploading...')
    // focus management: announce upload started and move focus to status
    const statusEl = document.getElementById(statusId)
    if (statusEl) statusEl.focus()
    xhr.send(fd)
  }

  function handleUploadClick() {
    if (live) {
      uploadLive()
    } else {
      setStatusText('Live upload disabled in this view.')
    }
  }

  return (
    <Card>
      <div className={`flex flex-col gap-4 ${rootClass}`}>
        <Heading level={3}>Upload audio</Heading>

        <input ref={inputRef} type="file" accept="audio/*" className="hidden" onChange={handleFileChange} />

        <div className={dropZoneClass} aria-hidden style={isDragging ? { outline: '2px solid var(--accent)', boxShadow: '0 0 14px rgba(0,194,255,0.06)', transform: 'scale(1.01)' } : {}}>
          <div className="text-white font-semibold">
            {hasFile ? `${file ? file.name : 'track.wav selected'}` : 'Drag & drop audio files or browse'}
          </div>
          <div className="text-muted text-sm">Supported formats: wav, mp3, m4a — max 20 MB</div>
        </div>

        <div className="flex justify-between items-center">
          <div className="flex gap-2 items-center">
            <Button variant="ghost" size="sm" onClick={handleSelectClick} onKeyDown={handleSelectKeyDown} disabled={disabledVisible} aria-disabled={disabledVisible} aria-label="Select audio file">
              Select file
            </Button>
            {progress !== null && (
              <div className="text-muted text-sm">{progress}%</div>
            )}
            {/* First-use hint next to select button */}
            <div className="ml-3">
              <FirstUseHint storageKey="zeusonic_hint_upload_v1" message="Upload an audio file to start — supported: wav, mp3, m4a." />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div aria-live="polite" id={statusId} className="text-sm text-muted" aria-atomic="true" tabIndex={-1}>
              {statusText}
            </div>

            {/* minimal visual indicator for processing */}
            <div aria-hidden className={`ml-2 rounded-full w-3 h-3 ${isUploadingVisible ? 'bg-accent glow-cyan processing-pulse' : 'bg-transparent'}`} />

            <Button variant="primary" disabled={disabledVisible || isUploadingVisible} size="md" onClick={handleUploadClick} aria-disabled={disabledVisible || isUploadingVisible} aria-busy={isUploadingVisible} aria-describedby={statusId}>
              {isUploadingVisible ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        </div>

        {/* Empty states */}
        {!hasFile && !isUploading && !statusText && <div className="mt-4"><EmptyState title="No uploads yet" body="Upload audio files to start generating sounds and tracks." /></div>}

        {maintenanceDisabled && <div className="mt-4"><EmptyState title="Uploads paused" body="Maintenance mode enabled. Try again shortly." /></div>}
      </div>
    </Card>
  )
}

export default React.memo(AudioUploadPanel)
