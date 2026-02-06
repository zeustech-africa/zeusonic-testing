"use client"

import React from 'react'
import { Music } from 'lucide-react'

const STYLES = [
  { id: 'electronic', name: 'Electronic', emoji: '🎛️', description: 'Synths & beats' },
  { id: 'amapiano', name: 'Amapiano', emoji: '🪘', description: 'Groovy house' },
  { id: 'afrobeats', name: 'Afrobeats', emoji: '🔊', description: 'Energetic drums' },
  { id: 'rnb', name: 'R&B', emoji: '💫', description: 'Smooth grooves' },
  { id: 'trap', name: 'Trap', emoji: '🎯', description: 'Hard hitting' },
  { id: 'edm', name: 'EDM', emoji: '⚡', description: 'High energy' },
  { id: 'jazz', name: 'Jazz', emoji: '🎷', description: 'Sophisticated' },
  { id: 'funk', name: 'Funk', emoji: '🕺', description: 'Funky grooves' },
]

interface StylePanelProps {
  style: string
  strength: number
  onStyleChange: (style: string, strength: number) => void
}

export default function StylePanel({
  style,
  strength,
  onStyleChange,
}: StylePanelProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-700 bg-gray-900">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Music size={20} />
          Style & Groove
        </h2>
        <p className="text-xs text-gray-400 mt-1">Choose a production style to influence arrangement</p>
      </div>

      {/* Styles */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {STYLES.map((s) => (
          <button
            key={s.id}
            onClick={() => onStyleChange(s.id, strength)}
            className={`w-full px-3 py-3 rounded-lg transition text-left ${
              style === s.id
                ? 'bg-gradient-to-r from-purple-600 to-purple-700 border border-purple-500'
                : 'bg-gray-800 border border-gray-700 hover:border-gray-600'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">{s.emoji}</span>
              <div>
                <p className="font-semibold text-white">{s.name}</p>
                <p className="text-xs text-gray-300">{s.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Strength Control */}
      <div className="px-4 py-4 border-t border-gray-700 bg-gray-900">
        <div className="mb-3">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-semibold text-white">Style Strength</label>
            <span className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-300">
              {Math.round(strength * 100)}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={strength}
            onChange={(e) => onStyleChange(style, parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Subtle</span>
            <span>Strong</span>
          </div>
        </div>

        {/* Info Box */}
        <div className="p-3 rounded bg-purple-900/20 border border-purple-700/30 text-xs text-purple-200 space-y-1">
          <p>✨ <strong>What this does:</strong></p>
          <ul className="list-disc list-inside space-y-1 mt-1">
            <li>Adjusts swing & timing</li>
            <li>Influences arrangement</li>
            <li>Guides instrument selection</li>
            <li>Shapes overall vibe</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
