"use client"

import React, { useRef, useState, useEffect, useMemo } from 'react'
import useLongPress from '../../hooks/useLongPress'
import EmptyState from '../ui/EmptyState'
import Card from '../ui/Card'
import Heading from '../ui/Heading'
import Button from '../ui/Button'
import FirstUseHint from '../ui/FirstUseHint'
import { config } from '../../lib/config'

type AudioUploadPanelProps = {
  isDragging?: boolean
  hasFile?: boolean
  isUploading?: boolean
  disabled?: boolean
  /** When true the component performs real uploads to the backend */
  live?: boolean
  /** Optional API key to use for uploads; falls back to localStorage 'ZEUSONIC_API_KEY' */
  apiKey?: string
}

export default function AudioUploadPanel({
  isDragging: propIsDragging,
  hasFile: propHasFile,
  isUploading: propIsUploading,
  disabled: propDisabled,
  live = false,
  apiKey: propApiKey,
}: AudioUploadPanelProps) {
  // internal state when not driven by props
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [disabled, setDisabled] = useState(false)
  const [maintenanceDisabled, setMaintenanceDisabled] = useState<boolean | undefined>(undefined)
  const [statusText, setStatusText] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<string | null>(null)
  const [progress, setProgress] = useState<number | null>(null)
  const [showUpgradeCTA, setShowUpgradeCTA] = useState(false)
  const statusId = useMemo(() => `upload-status-${Math.random().toString(36).slice(2,8)}`, [])

  // long-press hook for tooltips (touch) — target the local ref to avoid global queries
  const upgradeRef = useRef<HTMLDivElement | null>(null)
  const { onTouchStart, onTouchEnd } = useLongPress(() => {
    const el = upgradeRef.current
    if (!el) return
    el.classList.add('tooltip-active')
    setTimeout(() => { el.classList.remove('tooltip-active') }, 1500)
  }, 700)
  const inputRef = useRef<HTMLInputElement | null>(null)
  const pollingRef = useRef<number | null>(null)

  // derive visible states: prefer explicit props when provided
  const isDragging = propIsDragging ?? false
  const hasFile = propHasFile ?? Boolean(file)
  const isUploadingVisible = propIsUploading ?? isUploading
  const disabledVisible = propDisabled ?? disabled

  const dropZoneClass = `border-2 border-dashed rounded p-6 flex flex-col items-center justify-center gap-3 bg-base transition-all duration-150 ${
    isDragging ? 'ring-2' : 'border-surface'
  }`

  const rootClass = ` ${disabledVisible ? 'opacity-50 cursor-not-allowed' : ''}`

  useEffect(() => {
    return () => {
      // clear polling when unmounting
      if (pollingRef.current) {
        window.clearInterval(pollingRef.current)
      }
    }
  }, [])

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
      setJobStatus(null)
      setProgress(null)
      setShowUpgradeCTA(false)
    }
  }

  function getApiKey() {
    if (propApiKey) return propApiKey
    if (typeof window !== 'undefined') return window.localStorage.getItem('ZEUSONIC_API_KEY') || undefined
    return undefined
  }

  function startPolling(jobId: string) {
    // poll every 2s
    pollingRef.current = window.setInterval(async () => {
      try {
        const res = await fetch(`${config.apiUrl}/api/v1/audio/jobs/${jobId}`)
        if (!res.ok) {
          setStatusText('Error fetching job status — please try again')
          return
        }
        const data = await res.json()
        setJobStatus(data.status)
        if (data.status === 'completed') {
          setStatusText('Complete — your audio is ready. Check Library to download or preview it.')
          setJobStatus('completed')
          if (pollingRef.current) {
            window.clearInterval(pollingRef.current)
            pollingRef.current = null
          }
          setTimeout(() => setIsUploading(false), 200)
        } else if (data.status === 'failed') {
          setStatusText('Failed — we could not process this file. Try re-uploading or check format. If it persists, report an issue.')
          setJobStatus('failed')
          if (pollingRef.current) {
            window.clearInterval(pollingRef.current)
            pollingRef.current = null
          }
          setTimeout(() => setIsUploading(false), 200)
        } else if (data.status === 'processing') {
          setStatusText('Processing — we’re working on your audio now. This can take a few moments.')
          setJobStatus('processing')
        } else if (data.status === 'queued') {
          setStatusText('Queued — your file is in line and will be processed shortly.')
          setJobStatus('queued')
        } else {
          setStatusText(`Job ${data.status}`)
        }
      } catch (err) {
        setStatusText('Network error while checking job status — please check your connection')
      }
    }, 2000)
  }

  function uploadLive() {
    if (!file) {
      setStatusText('No file selected')
      return
    }
    const xhr = new XMLHttpRequest()
    const fd = new FormData()
    fd.append('file', file)

    const key = getApiKey()
    if (!key) {
      setStatusText('Missing API key — set ZEUSONIC_API_KEY in localStorage')
      setIsUploading(false)
      setDisabled(false)
      return
    }
    xhr.open('POST', `${config.apiUrl}/api/v1/audio/upload`)
    xhr.setRequestHeader('X-API-Key', key)

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
          const jobId = data.job_id
          setStatusText('Upload complete, polling job status...')
          startPolling(jobId)
        } catch (e) {
          setStatusText('Upload succeeded but response parse failed')
        }
      } else {
        // Try to parse response body for details
        try {
          const body = JSON.parse(xhr.responseText)
          if (body && body.detail) {
            setStatusText(String(body.detail))
            if (String(body.detail).toLowerCase().includes('upgrade')) {
              setShowUpgradeCTA(true)
            }
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
    if (process.env.NODE_ENV === 'development') console.info('[upload] attempt', { filename: file.name, owner: apiKey })

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
      // keep legacy behavior for stories: set uploading flag for short period and show success
      setIsUploading(true)
      setDisabled(true)
      setStatusText('Uploading (simulated)')
      setTimeout(() => {
        setIsUploading(false)
        setDisabled(false)
        setStatusText('Upload complete (simulated)')
        setFile(null)
      }, 1200)
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
            <div aria-hidden className={`ml-2 rounded-full w-3 h-3 ${jobStatus === 'processing' ? 'bg-accent glow-cyan processing-pulse' : jobStatus === 'failed' ? 'bg-danger' : 'bg-transparent'}`} />

            {showUpgradeCTA && (
              <div className="ml-2 flex items-center gap-2">
                <div ref={upgradeRef} className="tooltip" data-tooltip="Upgrade to unlock this feature" onTouchStart={onTouchStart} onTouchEnd={onTouchEnd}>
                  <Button variant="upgrade" size="sm" onClick={() => { if (process.env.NODE_ENV === 'development') console.info('[gated] upgrade-click'); window.alert('Upgrade flow not implemented') }} aria-disabled={false} aria-describedby={statusId} aria-label="Upgrade to unlock — opens upgrade dialog">
                    Upgrade to unlock
                  </Button>
                </div>
                <div className="upgrade-hint">
                  {/* First-use hint for the upgrade CTA */}
                  <FirstUseHint storageKey="zeusonic_hint_upgrade_v1" message="Upgrade removes limits and unlocks downloads and longer processing times." />
                </div>
              </div>
            )}

            <Button variant="primary" disabled={disabledVisible || isUploadingVisible} size="md" onClick={handleUploadClick} aria-disabled={disabledVisible || isUploadingVisible} aria-busy={isUploadingVisible} aria-describedby={statusId}>
              {isUploadingVisible ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        </div>

        {/* Empty states */}
        {!hasFile && !isUploading && !statusText && <div className="mt-4"><EmptyState title="No uploads yet" body="Upload audio files to start generating sounds and tracks." /></div>}

        {jobStatus === 'failed' && <div className="mt-4"><EmptyState title="Job failed" body="Something went wrong while processing. Try re-uploading or check file format." /></div>}
      </div>
    </Card>
  )
}

export default React.memo(AudioUploadPanel)
