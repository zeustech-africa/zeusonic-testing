import './globals.css'

export const metadata = {
  title: {
    default: 'Zeusonic · by ZeusTech',
    template: '%s · Zeusonic',
  },
 description: 'Zeusonic is a premium AI-powered music creation platform by ZeusTech.',
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
          <div className="max-w-6xl mx-auto px-6 py-4" style={{ position: 'relative' }}>
            <div className="header-branding">
              <img src="/brand/zeustech/logo.png" alt="ZeusTech" className="h-6 w-auto" />
              <span className="branding-text">Zeusonic · by ZeusTech</span>
            </div>

            <div className="header-actions">
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
