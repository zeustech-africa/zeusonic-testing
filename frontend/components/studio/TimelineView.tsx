"use client"

import React from 'react'
import { Trash2, Eye, EyeOff } from 'lucide-react'
import type { Track } from '../StudioInterface'

interface TimelineViewProps {
  project: any
  tracks: Track[]
  selectedTrackId: string | null
  currentTime: number
  isPlaying: boolean
  onSelectTrack: (id: string) => void
  onRemoveTrack: (id: string) => void
}

export default function TimelineView({
  project,
  tracks,
  selectedTrackId,
  currentTime,
  isPlaying,
  onSelectTrack,
  onRemoveTrack,
}: TimelineViewProps) {
  const maxDuration = Math.max(...tracks.map(t => t.duration || 30), 30)
  const pixelsPerSecond = 50

  return (
    <div className="flex-1 flex overflow-hidden bg-gray-950">
      {/* Track List */}
      <div className="w-48 border-r border-gray-700 bg-gray-900 overflow-y-auto">
        {tracks.map((track, idx) => (
          <div
            key={track.id}
            onClick={() => onSelectTrack(track.id)}
            className={`px-3 py-3 border-b border-gray-800 cursor-pointer transition ${
              selectedTrackId === track.id ? 'bg-blue-900/50' : 'hover:bg-gray-800'
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{track.name}</p>
                <p className="text-xs text-gray-400">{track.instrumentType || 'Base Track'}</p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onRemoveTrack(track.id)
                }}
                className="p-1 rounded hover:bg-red-900/50 transition opacity-0 hover:opacity-100"
              >
                <Trash2 size={14} className="text-red-400" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Timeline Grid */}
      <div className="flex-1 overflow-x-auto bg-gray-950">
        <div className="relative" style={{ minWidth: `${maxDuration * pixelsPerSecond}px` }}>
          {/* Ruler */}
          <div className="sticky top-0 h-8 bg-gray-800 border-b border-gray-700 flex items-center">
            {Array.from({ length: Math.ceil(maxDuration / 5) + 1 }).map((_, i) => {
              const time = i * 5
              return (
                <div
                  key={i}
                  className="border-l border-gray-600 h-full flex items-center px-1"
                  style={{ width: `${5 * pixelsPerSecond}px` }}
                >
                  <span className="text-xs text-gray-400">{time}s</span>
                </div>
              )
            })}
          </div>

          {/* Tracks */}
          {tracks.map((track) => (
            <div
              key={track.id}
              className="h-16 border-b border-gray-800 bg-gray-950 hover:bg-gray-900/50 transition relative"
              onClick={() => onSelectTrack(track.id)}
            >
              {/* Track Background */}
              <div className="absolute inset-0 flex items-center px-2">
                <div className="flex-1 h-12 bg-gray-800 rounded opacity-30"></div>
              </div>

              {/* Waveform Visualization */}
              <div className="absolute inset-0 flex items-center px-2">
                <div className="flex-1 h-12 bg-gradient-to-b from-blue-500 to-blue-700 rounded opacity-60 flex items-center justify-center">
                  <div className="flex items-end gap-0.5 h-8 justify-center w-full">
                    {Array.from({ length: 20 }).map((_, i) => (
                      <div
                        key={i}
                        className="flex-1 bg-blue-300 opacity-60 rounded-sm"
                        style={{
                          height: `${30 + Math.random() * 50}%`,
                        }}
                      ></div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Duration Label */}
              <div className="absolute left-2 top-1 text-xs text-blue-200 pointer-events-none">
                {track.duration.toFixed(1)}s
              </div>
            </div>
          ))}

          {/* Playhead */}
          <div
            className="absolute top-0 w-0.5 bg-green-500 h-full pointer-events-none z-10"
            style={{
              left: `${currentTime * pixelsPerSecond}px`,
              boxShadow: '0 0 8px rgba(34, 197, 94, 0.5)',
            }}
          ></div>
        </div>
      </div>
    </div>
  )
}
