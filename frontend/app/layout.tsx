import './globals.css'
import Image from 'next/image'

export const metadata = {
  title: 'Zeusonic',
  description: 'Zeusonic — luxury music platform',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-base text-muted min-h-screen">
        <header className="w-full border-b border-surface">
          <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img src="/assets/branding/logo-full.svg" alt="ZEUSONIC by ZeusTech" className="h-10 md:h-12" />
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
