import './globals.css'
import Image from 'next/image'

export const metadata = {
  title: {
    default: 'Zeusonic · by ZeusTech',
    template: '%s · Zeusonic',
  },
  description: 'Zeusonic is a premium AI-powered music creation platform 
by ZeusTech.',
  icons: {
    icon: '/favicon.png',
  },
  openGraph: {
    title: 'Zeusonic · by ZeusTech',
    description: 'Premium AI music creation by ZeusTech.',
    type: 'website',
    siteName: 'Zeusonic',
  },
  twitter: {
    card: 'summary',
    title: 'Zeusonic · by ZeusTech',
    description: 'Premium AI music creation by ZeusTech.',
  },
}


export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-base text-muted min-h-screen">
        <header className="w-full border-b border-surface">
          <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img src="/brand/zeusonic/logo.png" alt="Zeusonic" className="h-10 md:h-12 w-auto" />
              <span className="text-muted text-sm hidden sm:inline">by</span>
              <img src="/brand/zeustech/logo.png" alt="ZeusTech" className="h-6 w-auto hidden sm:inline opacity-80" />
            </div>

            <div className="flex items-center gap-3">
              <button className="text-sm text-muted">Sign in</button>
              <button className="btn btn-primary">Get started</button>
            </div>
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-6 py-12">{children}</main>
      </body>
    </html>
  )
}
