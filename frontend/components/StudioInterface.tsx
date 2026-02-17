"use client"

import React from 'react'

export interface Track {
  id: string
  name: string
  type: 'base' | 'instrument'
  instrumentType?: string
  duration?: number
  volume?: number
  pan?: number
  presence?: number
  energy?: number
  space?: number
  muted?: boolean
  soloed?: boolean
}

interface StudioInterfaceProps {
  projectId?: string
}

export default function StudioInterface({ projectId }: StudioInterfaceProps) {
  if (process.env.NODE_ENV === 'development') {
    console.info('[Studio] StudioInterface is deprecated. Use AudioProcessor in /studio instead.', { projectId })
  }
  return null
}
