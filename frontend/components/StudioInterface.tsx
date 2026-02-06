"use client"

import React, { useState, useEffect } from 'react'
import { Play, Pause, Volume2, RotateCcw, Download, Music } from 'lucide-react'
import StudioTopBar from './studio/StudioTopBar'
import SoundLibrary from './studio/SoundLibrary'
import TimelineView from './studio/TimelineView'
import TrackMixer from './studio/TrackMixer'
import StylePanel from './studio/StylePanel'

export interface Track {
  id: string
  name: string
  type: 'base' | 'instrument'
  instrumentType?: string
  soundVariant?: string
  duration: number
  volume: number
  pan: number
  muted: boolean
  soloed: boolean
  presence: number
  energy: number
  space: number
}

export interface Project {
  id: string
  name: string
  baseTrack: Track | null
  tracks: Track[]
  tempo: number
  key: string
  style?: string
  styleStrength?: number
}

interface StudioInterfaceProps {
  apiKey: string
  projectId?: string
}

export default function StudioInterface({ apiKey, projectId }: StudioInterfaceProps) {
  const [project, setProject] = useState<Project>({
    id: projectId || 'new-project',
    name: 'Untitled Project',
    baseTrack: null,
    tracks: [],
    tempo: 120,
    key: 'C',
    style: 'Electronic',
    styleStrength: 0.5,
  })

  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [selectedTrackId, setSelectedTrackId] = useState<string | null>(null)
  const [showLibrary, setShowLibrary] = useState(false)
  const [showStylePanel, setShowStylePanel] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [playbackProgress, setPlaybackProgress] = useState(0)

  // Mock playback timer
  useEffect(() => {
    if (!isPlaying) return

    const interval = setInterval(() => {
      setCurrentTime(prev => {
        const maxDuration = Math.max(
          project.baseTrack?.duration || 0,
          Math.max(...project.tracks.map(t => t.duration), 0)
        )
        return prev >= maxDuration ? 0 : prev + 0.1
      })
    }, 100)

    return () => clearInterval(interval)
  }, [isPlaying, project])

  const handleAddTrack = (instrumentType: string, soundVariant: string) => {
    const newTrack: Track = {
      id: `track-${Date.now()}`,
      name: `${instrumentType} - ${soundVariant}`,
      type: 'instrument',
      instrumentType,
      soundVariant,
      duration: project.baseTrack?.duration || 30,
      volume: -6,
      pan: 0,
      muted: false,
      soloed: false,
      presence: 50,
      energy: 50,
      space: 30,
    }

    setProject({
      ...project,
      tracks: [...project.tracks, newTrack],
    })

    setSelectedTrackId(newTrack.id)
    setShowLibrary(false)
  }

  const handleUpdateTrack = (trackId: string, updates: Partial<Track>) => {
    setProject({
      ...project,
      tracks: project.tracks.map(t =>
        t.id === trackId ? { ...t, ...updates } : t
      ),
    })
  }

  const handleRemoveTrack = (trackId: string) => {
    setProject({
      ...project,
      tracks: project.tracks.filter(t => t.id !== trackId),
    })
    if (selectedTrackId === trackId) {
      setSelectedTrackId(null)
    }
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      // Call backend export endpoint
      const response = await fetch(`https://zeusonic-api.onrender.com/api/v1/audio/export`, {
        method: 'POST',
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          projectId: project.id,
          tempo: project.tempo,
          key: project.key,
          style: project.style,
          styleStrength: project.styleStrength,
          tracks: [
            project.baseTrack,
            ...project.tracks,
          ].filter(Boolean),
        }),
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${project.name}.wav`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  const allTracks = project.baseTrack ? [project.baseTrack, ...project.tracks] : project.tracks
  const selectedTrack = allTracks.find(t => t.id === selectedTrackId)

  return (
    <div className="flex flex-col h-screen bg-black text-white">
      {/* Top Bar */}
      <StudioTopBar
        project={project}
        onProjectNameChange={(name) => setProject({ ...project, name })}
        onTempoChange={(tempo) => setProject({ ...project, tempo })}
        onKeyChange={(key) => setProject({ ...project, key })}
      />

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel - Sound Library */}
        <div className={`${showLibrary ? 'w-80' : 'w-0'} transition-all duration-300 bg-gray-900 border-r border-gray-700 overflow-hidden`}>
          {showLibrary && <SoundLibrary onSelectSound={handleAddTrack} />}
        </div>

        {/* Center - Timeline */}
        <div className="flex-1 flex flex-col overflow-hidden bg-gray-950">
          <TimelineView
            project={project}
            tracks={allTracks}
            selectedTrackId={selectedTrackId}
            currentTime={currentTime}
            isPlaying={isPlaying}
            onSelectTrack={setSelectedTrackId}
            onRemoveTrack={handleRemoveTrack}
          />

          {/* Transport Bar */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-700 bg-gray-900">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-2 rounded-lg bg-green-600 hover:bg-green-700 transition"
              >
                {isPlaying ? <Pause size={20} /> : <Play size={20} />}
              </button>
              <button
                onClick={() => setCurrentTime(0)}
                className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition"
              >
                <RotateCcw size={20} />
              </button>
            </div>

            <div className="flex items-center gap-2 text-sm text-gray-300">
              <span>{String(Math.floor(currentTime / 60)).padStart(2, '0')}:{String(Math.floor(currentTime % 60)).padStart(2, '0')}</span>
              <div className="w-48 h-1 bg-gray-700 rounded">
                <div
                  className="h-full bg-green-600 rounded"
                  style={{ width: `${playbackProgress}%` }}
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowLibrary(!showLibrary)}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 transition flex items-center gap-2"
              >
                <Music size={16} />
                Add Sound
              </button>
              <button
                onClick={() => setShowStylePanel(!showStylePanel)}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 transition"
              >
                Style
              </button>
              <button
                onClick={handleExport}
                disabled={isExporting || !project.baseTrack}
                className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 transition flex items-center gap-2"
              >
                <Download size={16} />
                {isExporting ? 'Exporting...' : 'Export'}
              </button>
            </div>
          </div>
        </div>

        {/* Right Panel - Mixer */}
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
