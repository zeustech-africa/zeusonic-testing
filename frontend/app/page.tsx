export default function Home() {
  return (
    <section className="min-h-[60vh] flex flex-col items-center justify-center text-center gap-6">
      <h1 className="text-4xl md:text-5xl font-bold text-white">ZEUSONIC</h1>
      <p className="text-lg text-muted max-w-2xl">Luxury AI music tools for creators. Upload an audio file to analyze and preview your track.</p>
      <div className="flex gap-4">
        <button className="btn btn-primary">Upload &amp; Analyze</button>
        <button className="btn btn-ghost">Learn more</button>
      </div>
    </section>
  )
}
