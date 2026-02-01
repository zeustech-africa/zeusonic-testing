import Container from './ui/Container'
import Heading from './ui/Heading'
import Card from './ui/Card'
import Divider from './ui/Divider'
import Button from './ui/Button'
import Link from 'next/link'
import SubscriptionBadge from './SubscriptionBadge'
import SubscriptionAura from './SubscriptionAura'
import BetaArea from './BetaArea'
import BetaOnboarding from './BetaOnboarding'
import BetaSupport from './BetaSupport'

export default function AppLayout({ children, title }: { children: React.ReactNode; title?: string }) {
  return (
    <div className="min-h-screen bg-base text-white">
      <div className="border-b border-surface">
        <Container>
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center gap-4">
              <img src="/brand/zeusonic/logo.png" alt="Zeusonic" className="h-10 w-auto" />
<span className="text-muted text-sm hidden sm:inline">by</span>
<img src="/brand/zeustech/logo.png" alt="ZeusTech" className="h-6 w-auto hidden sm:inline opacity-80" />
            </div>
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/dashboard" className="text-muted hover:text-white">Dashboard</Link>
              <Link href="/generate" className="text-muted hover:text-white">Generate</Link>
              <Link href="/library" className="text-muted hover:text-white">Library</Link>
              <div className="ml-4 flex items-center gap-2">
                <Button variant="secondary" size="sm">Preview</Button>
                <Button variant="primary" size="sm">New</Button>
              </div>
              <div className="ml-6 flex items-center gap-2">
                <SubscriptionBadge />
                <BetaArea />
              </div>
            </nav>
            <div className="md:hidden">
              {/* Mobile compact header actions */}
              <Button variant="ghost" size="sm">Menu</Button>
            </div>
            <BetaOnboarding />
            <UploadDisabledBanner />
          </div>
        </Container>
      </div>

      <main className="py-8">
        <Container>
          {title && <div className="mb-4"><Heading level={1}>{title}</Heading><Divider /></div>}

          <div className="studio-grid">
            <aside className="left-rail" role="navigation" aria-label="Tool rail">
              <div className="flex flex-col gap-3" role="tablist" aria-orientation="vertical">
                <Button variant="ghost" size="sm" aria-pressed={false}>Samples</Button>
                <Button variant="ghost" size="sm" aria-pressed={false}>Instruments</Button>
                <Button variant="ghost" size="sm" aria-pressed={false}>Effects</Button>
                <div className="mt-4">
                  <SubscriptionBadge />
                </div>
              </div>
            </aside>

            <section id="center-canvas" className="center-canvas bg-surface shadow-soft relative">
              <SubscriptionAura />
              {children}
              <div className="absolute inset-0 pointer-events-none" />
            </section>

            <aside className="right-panel bg-surface shadow-soft" aria-label="AI Controls">
              <div className="flex flex-col gap-3">
                <div className="font-semibold">AI Controls</div>
                <div className="text-muted text-sm">Parameters and model controls</div>
              </div>
              <div className="mt-4 text-muted text-sm">
                <BetaSupport />
              </div>
            </aside>
          </div>
        </Container>
      </main>

      {/* Mobile bottom nav + floating action button */}
      <nav className="mobile-bottom-nav" role="navigation" aria-label="Mobile navigation">
        <button className="btn btn-secondary" aria-label="Home" onClick={() => { if (process.env.NODE_ENV === 'development') console.info('[nav] home-click') }}>Home</button>
        <button className="btn btn-secondary" aria-label="Generate" onClick={() => { if (process.env.NODE_ENV === 'development') console.info('[nav] generate-click') }}>Generate</button>
        <button className="btn btn-secondary" aria-label="Library" onClick={() => { if (process.env.NODE_ENV === 'development') console.info('[nav] library-click') }}>Library</button>
      </nav>
      <button className="fab" aria-label="New" onClick={() => { if (process.env.NODE_ENV === 'development') console.info('[action] fab-click') }} aria-haspopup="true">+</button>
    </div>
  )
}
