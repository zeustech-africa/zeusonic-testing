import AppLayout from '../../components/AppLayout'
import Heading from '../../components/ui/Heading'
import Card from '../../components/ui/Card'

export default function LibraryPage() {
  return (
    <AppLayout title="Library">
      <div className="space-y-6">
        <Heading level={2}>Your Library</Heading>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>Track list (placeholder)</Card>
          <Card>Playlists (placeholder)</Card>
          <Card>Tags / Filters (placeholder)</Card>
        </div>
      </div>
    </AppLayout>
  )
}
