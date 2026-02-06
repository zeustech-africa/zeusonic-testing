"use client"

import React from 'react'

interface StudioTopBarProps {
  project: {
    name: string
    tempo: number
    key: string
  }
  onProjectNameChange: (name: string) => void
  onTempoChange: (tempo: number) => void
  onKeyChange: (key: string) => void
}

const KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

export default function StudioTopBar({
  project,
  onProjectNameChange,
  onTempoChange,
  onKeyChange,
}: StudioTopBarProps) {
  return (
    <div className="flex items-center justify-between px-8 py-4 border-b border-gray-700 bg-gray-900">
      {/* Left - Project Info */}
      <div className="flex items-center gap-6">
        <input
          type="text"
          value={project.name}
          onChange={(e) => onProjectNameChange(e.target.value)}
          className="bg-transparent text-2xl font-bold text-white border-b-2 border-transparent hover:border-gray-500 focus:border-blue-500 outline-none transition"
          placeholder="Untitled Project"
        />

        <div className="flex items-center gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-400 uppercase">Tempo</label>
            <div className="flex items-center gap-1">
              <input
                type="number"
                value={project.tempo}
                onChange={(e) => onTempoChange(parseInt(e.target.value))}
                min="60"
                max="200"
                className="w-16 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-white text-sm focus:border-blue-500 outline-none"
              />
              <span className="text-xs text-gray-400">BPM</span>
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-400 uppercase">Key</label>
            <select
              value={project.key}
              onChange={(e) => onKeyChange(e.target.value)}
              className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-white text-sm focus:border-blue-500 outline-none"
            >
              {KEYS.map(key => (
                <option key={key} value={key}>{key}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Right - Session Info */}
      <div className="flex items-center gap-4 text-sm text-gray-400">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500"></div>
          Session Active
        </div>
        <div className="text-xs text-gray-500">
          {new Date().toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}
