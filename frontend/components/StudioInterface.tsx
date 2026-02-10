"use client"

import React from 'react'

export interface Track {
  id: string
  name: string
  type: 'base' | 'instrument'
  instrumentType?: string
  interface StudioInterfaceProps {
    projectId?: string
  }

  export default function StudioInterface({ projectId }: StudioInterfaceProps) {
    if (process.env.NODE_ENV === 'development') {
      console.info('[studio] StudioInterface is deprecated. Use AudioProcessor in /studio instead.', { projectId })
    }
    return null
  }
        {selectedTrack && (
          <div className="w-64 border-l border-gray-700 bg-gray-900 overflow-y-auto">
            <TrackMixer
              track={selectedTrack}
              onUpdateTrack={(updates) => handleUpdateTrack(selectedTrack.id, updates)}
            />
          </div>
        )}

        {/* Style Panel */}
        {showStylePanel && (
          <div className="w-72 border-l border-gray-700 bg-gray-900 overflow-y-auto">
            <StylePanel
              style={project.style || 'Electronic'}
              strength={project.styleStrength || 0.5}
              onStyleChange={(style, strength) =>
                setProject({ ...project, style, styleStrength: strength })
              }
            />
          </div>
        )}
      </div>
    </div>
  )
}
