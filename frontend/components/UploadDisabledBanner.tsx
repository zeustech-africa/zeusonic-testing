"use client"

import React, { useEffect, useState } from 'react'
import { config } from '../lib/config'

export default function UploadDisabledBanner() {
  const [disabled, setDisabled] = useState<boolean | undefined>(undefined)

  useEffect(() => {
    let mounted = true
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3000)

    fetch(`${config.apiUrl}/api/v1/meta`, { signal: controller.signal })
      .then((r) => r.json())
      .then((d) => { if (!mounted) return; setDisabled(Boolean(d.disable_uploads)) })
      .catch(() => { if (mounted) setDisabled(false) })
      .finally(() => clearTimeout(timeout))

    return () => { mounted = false; controller.abort(); clearTimeout(timeout) }
  }, [])

  if (!disabled) return null

  return (
    <div className="maintenance-banner" role="status" aria-live="polite">
      Uploads temporarily paused for maintenance.
    </div>
  )
}
