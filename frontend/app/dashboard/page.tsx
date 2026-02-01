import AppLayout from '../../components/AppLayout'
import Heading from '../../components/ui/Heading'
import Card from '../../components/ui/Card'
import AudioUploadPanel from '../../components/features/AudioUploadPanel'
import Timeline from '../../components/Timeline'
import EmptyState from '../../components/ui/EmptyState'

export default function DashboardPage() {
  return (
    <AppLayout title="Dashboard">
      <div className="space-y-6">
        <Heading level={2}>Overview</Heading>

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
  )
}
