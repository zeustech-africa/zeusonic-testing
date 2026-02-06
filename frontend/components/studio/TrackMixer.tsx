"use client"

import React from 'react'
import { Volume2, Zap, Wind, Waves } from 'lucide-react'
import type { Track } from '../StudioInterface'

interface TrackMixerProps {
  track: Track
  onUpdateTrack: (updates: Partial<Track>) => void
}

export default function TrackMixer({ track, onUpdateTrack }: TrackMixerProps) {
  const handleVolumeChange = (value: number) => {
    onUpdateTrack({ volume: value })
  }

  const handlePanChange = (value: number) => {
    onUpdateTrack({ pan: value })
  }

  const handlePresenceChange = (value: number) => {
    onUpdateTrack({ presence: value })
  }

  const handleEnergyChange = (value: number) => {
    onUpdateTrack({ energy: value })
  }

  const handleSpaceChange = (value: number) => {
    onUpdateTrack({ space: value })
  }

  const handleMuteToggle = () => {
    onUpdateTrack({ muted: !track.muted })
  }

  const handleSoloToggle = () => {
    onUpdateTrack({ soloed: !track.soloed })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-700 bg-gray-900">
        <h2 className="text-lg font-bold text-white truncate">{track.name}</h2>
        <p className="text-xs text-gray-400 mt-1 capitalize">{track.instrumentType || 'Track'}</p>
      </div>

      {/* Controls */}
      <div className="flex-1 px-4 py-4 space-y-6 overflow-y-auto">
        {/* Mute / Solo */}
        <div className="flex gap-2">
          <button
            onClick={handleMuteToggle}
            className={`flex-1 py-2 rounded font-medium text-sm transition ${
              track.muted
                ? 'bg-red-900/50 text-red-200'
                : 'bg-gray-700 text-gray-200 hover:bg-gray-600'
            }`}
          >
            {track.muted ? '🔇 Muted' : '🔊 Mute'}
          </button>
          <button
            onClick={handleSoloToggle}
            className={`flex-1 py-2 rounded font-medium text-sm transition ${
              track.soloed
                ? 'bg-yellow-900/50 text-yellow-200'
                : 'bg-gray-700 text-gray-200 hover:bg-gray-600'
            }`}
          >
            {track.soloed ? '👂 Solo' : 'Solo'}
          </button>
        </div>

        {/* Volume */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-white flex items-center gap-2">
              <Volume2 size={16} />
              Volume
            </label>
            <span className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-300">
              {track.volume.toFixed(1)} dB
            </span>
          </div>
          <input
            type="range"
            min="-20"
            max="6"
            step="0.5"
            value={track.volume}
            onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>-20 dB</span>
            <span>0 dB</span>
            <span>+6 dB</span>
          </div>
        </div>

        {/* Pan */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-white">Pan</label>
            <span className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-300">
              {track.pan > 0 ? '→' : track.pan < 0 ? '←' : '◆'} {Math.abs(track.pan).toFixed(0)}%
            </span>
          </div>
          <input
            type="range"
            min="-100"
            max="100"
            step="5"
            value={track.pan}
            onChange={(e) => handlePanChange(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>

        {/* Producer Controls */}
        <div className="pt-4 border-t border-gray-700">
          <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Producer Controls</p>

          {/* Presence */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-white flex items-center gap-2">
                <Zap size={14} />
                Presence
              </label>
              <span className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-300">
                {track.presence.toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={track.presence}
              onChange={(e) => handlePresenceChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-yellow-500"
            />
            <p className="text-xs text-gray-400 mt-1">High-frequency clarity</p>
          </div>

          {/* Energy */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-white flex items-center gap-2">
                <Zap size={14} />
                Energy
              </label>
              <span className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-300">
                {track.energy.toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={track.energy}
              onChange={(e) => handleEnergyChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-red-500"
            />
            <p className="text-xs text-gray-400 mt-1">Intensity & drive</p>
          </div>

          {/* Space */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-white flex items-center gap-2">
                <Wind size={14} />
                Space
              </label>
              <span className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-300">
                {track.space.toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={track.space}
              onChange={(e) => handleSpaceChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
            <p className="text-xs text-gray-400 mt-1">Reverb & depth</p>
          </div>
        </div>

        {/* AI Note */}
        <div className="mt-6 p-3 rounded bg-blue-900/30 border border-blue-700/50">
          <p className="text-xs text-blue-200">
            💡 AI is automatically matching this instrument to your project's tempo and key.
          </p>
        </div>
      </div>
    </div>
  )
}
