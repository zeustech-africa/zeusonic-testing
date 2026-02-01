import React from 'react'
import FirstUseHint from './ui/FirstUseHint'

function TimelineInner({ children }: { children?: React.ReactNode }) {
  return (
    <div className="rounded-md bg-gradient-to-b from-transparent to-black/10 p-4" style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Roboto Mono, "Courier New", monospace' }}>
      <div className="w-full h-40 bg-[linear-gradient(90deg,#00121a,#031428)] rounded-md overflow-hidden">
        {children ? children : (
          <div className="h-full flex flex-col items-center justify-center text-muted gap-2">
            <div>No waveform yet — upload audio to begin</div>
            <div><FirstUseHint storageKey="zeusonic_hint_timeline_v1" message="Your waveform will appear here after upload. Use Upload to add tracks." /></div>
          </div>
        )}
      </div>
    </div>
  )
}

export default React.memo(TimelineInner)
