"use client"

import AppLayout from '../../components/AppLayout'
import Heading from '../../components/ui/Heading'
import Card from '../../components/ui/Card'
import AudioUploadPanel from '../../components/features/AudioUploadPanel'
import RequireAuth from '../../components/auth/RequireAuth'

export default function GeneratePage() {
  return (
    <RequireAuth>
      <AppLayout title="Generate">
        <div className="space-y-6">
          <Heading level={2}>Generation</Heading>

          {/* Audio upload panel included as the primary feature area (live integration enabled) */}
          <AudioUploadPanel live />

          <Card>Recent results (placeholder)</Card>
        </div>
      </AppLayout>
    </RequireAuth>
  )
}
