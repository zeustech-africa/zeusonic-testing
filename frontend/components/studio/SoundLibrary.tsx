"use client"

import React, { useState } from 'react'
import { Zap, Volume2, Waves, Wind } from 'lucide-react'

const INSTRUMENT_LIBRARY = {
  drums: {
    name: 'Drums',
    icon: '🥁',
    sounds: [
      { id: '808-kick', name: 'Heavy 808', variant: '808-dark', description: 'Deep sub bass kick' },
      { id: 'acoustic-kick', name: 'Acoustic Kick', variant: 'acoustic', description: 'Real drum kit' },
      { id: 'punchy-kick', name: 'Punchy Kick', variant: 'punchy', description: 'Tight punch' },
      { id: 'snare-crisp', name: 'Crisp Snare', variant: 'crisp', description: 'Sharp attack' },
      { id: 'snare-fat', name: 'Fat Snare', variant: 'fat', description: 'Full body' },
      { id: 'hihat-closed', name: 'Closed Hat', variant: 'closed', description: 'Tight cymbal' },
      { id: 'hihat-open', name: 'Open Hat', variant: 'open', description: 'Shimmering' },
      { id: 'tom-high', name: 'High Tom', variant: 'high', description: 'Pitched drum' },
    ],
  },
  bass: {
    name: 'Bass',
    icon: '🎸',
    sounds: [
      { id: 'sub-bass', name: 'Sub Bass', variant: 'sub', description: 'Deep resonant' },
      { id: 'synth-bass-warm', name: 'Warm Bass', variant: 'warm', description: 'Smooth synth' },
      { id: 'synth-bass-bright', name: 'Bright Bass', variant: 'bright', description: 'Crisp tone' },
      { id: 'acoustic-bass', name: 'Acoustic Bass', variant: 'acoustic', description: 'Natural tone' },
      { id: 'funk-bass', name: 'Funk Bass', variant: 'funk', description: 'Groovy slap' },
    ],
  },
  guitar: {
    name: 'Guitar',
    icon: '🎸',
    sounds: [
      { id: 'acoustic-guitar', name: 'Acoustic', variant: 'acoustic', description: 'Clean strums' },
      { id: 'electric-clean', name: 'Clean Electric', variant: 'clean', description: 'Bright jangly' },
      { id: 'electric-warm', name: 'Warm Electric', variant: 'warm', description: 'Creamy tone' },
      { id: 'electric-distorted', name: 'Distorted', variant: 'distorted', description: 'Heavy crunch' },
      { id: 'fingerpicking', name: 'Fingerpicking', variant: 'fingerpicking', description: 'Delicate' },
    ],
  },
  piano: {
    name: 'Piano',
    icon: '🎹',
    sounds: [
      { id: 'grand-piano-bright', name: 'Bright Grand', variant: 'bright', description: 'Crisp tone' },
      { id: 'grand-piano-warm', name: 'Warm Grand', variant: 'warm', description: 'Rich resonance' },
      { id: 'electric-piano', name: 'Electric Piano', variant: 'electric', description: 'Retro vibes' },
      { id: 'harp', name: 'Harp', variant: 'harp', description: 'Ethereal' },
    ],
  },
  trumpet: {
    name: 'Trumpet',
    icon: '🎺',
    sounds: [
      { id: 'trumpet-soft', name: 'Soft Trumpet', variant: 'soft', description: 'Mellow warm' },
      { id: 'trumpet-bright', name: 'Bright Trumpet', variant: 'bright', description: 'Cutting edge' },
      { id: 'trumpet-muted', name: 'Muted Trumpet', variant: 'muted', description: 'Vintage feel' },
      { id: 'horn-section', name: 'Horn Section', variant: 'section', description: 'Rich ensemble' },
    ],
  },
  synth: {
    name: 'Synth',
    icon: '🎛️',
    sounds: [
      { id: 'synth-pad-lush', name: 'Lush Pad', variant: 'lush', description: 'Atmospheric' },
      { id: 'synth-pad-bright', name: 'Bright Pad', variant: 'bright', description: 'Shimmering' },
      { id: 'synth-lead-sharp', name: 'Sharp Lead', variant: 'sharp', description: 'Cutting tone' },
      { id: 'synth-lead-warm', name: 'Warm Lead', variant: 'warm', description: 'Smooth flow' },
      { id: 'synth-pluck', name: 'Synth Pluck', variant: 'pluck', description: 'Staccato' },
    ],
  },
  fx: {
    name: 'Effects & Textures',
    icon: '✨',
    sounds: [
      { id: 'ambient-pad', name: 'Ambient Pad', variant: 'ambient', description: 'Dreamy layer' },
      { id: 'reverse-cymbal', name: 'Reverse Cymbal', variant: 'reverse', description: 'Build up' },
      { id: 'vinyl-crackle', name: 'Vinyl Crackle', variant: 'vinyl', description: 'Vintage' },
      { id: 'white-noise-whoosh', name: 'Whoosh', variant: 'whoosh', description: 'Transition' },
      { id: 'digital-glitch', name: 'Digital Glitch', variant: 'glitch', description: 'Modern edge' },
    ],
  },
}

interface SoundLibraryProps {
  onSelectSound: (instrumentType: string, soundVariant: string) => void
}

export default function SoundLibrary({ onSelectSound }: SoundLibraryProps) {
  const [expandedCategory, setExpandedCategory] = useState<string>('drums')
  const [hoveredSound, setHoveredSound] = useState<string | null>(null)

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-700">
        <h2 className="text-lg font-bold text-white">Sound Library</h2>
        <p className="text-xs text-gray-400 mt-1">Select sounds to add to your arrangement</p>
      </div>

      {/* Categories */}
      <div className="flex-1 overflow-y-auto">
        {Object.entries(INSTRUMENT_LIBRARY).map(([categoryId, category]) => (
          <div key={categoryId} className="border-b border-gray-800">
            <button
              onClick={() => setExpandedCategory(expandedCategory === categoryId ? '' : categoryId)}
              className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-800 transition text-left"
            >
              <span className="text-xl">{(category as any).icon}</span>
              <div className="flex-1">
                <h3 className="font-semibold text-white">{(category as any).name}</h3>
              </div>
              <span className={`text-gray-400 transition ${expandedCategory === categoryId ? 'rotate-180' : ''}`}>
                ▼
              </span>
            </button>

            {/* Sounds in Category */}
            {expandedCategory === categoryId && (
              <div className="bg-gray-800/50 px-4 py-2">
                {(category as any).sounds.map((sound: any) => (
                  <button
                    key={sound.id}
                    onMouseEnter={() => setHoveredSound(sound.id)}
                    onMouseLeave={() => setHoveredSound(null)}
                    onClick={() => onSelectSound(categoryId, sound.variant)}
                    className="w-full px-3 py-3 rounded mb-2 bg-gray-700 hover:bg-blue-600 transition group"
                  >
                    <div className="flex items-start justify-between">
                      <div className="text-left flex-1">
                        <p className="font-medium text-white text-sm">{sound.name}</p>
                        <p className="text-xs text-gray-300">{sound.description}</p>
                      </div>
                      {hoveredSound === sound.id && (
                        <button
                          className="px-3 py-1 rounded text-xs bg-green-600 hover:bg-green-700 transition text-white font-medium"
                          onClick={(e) => {
                            e.stopPropagation()
                            onSelectSound(categoryId, sound.variant)
                          }}
                        >
                          Add
                        </button>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer Info */}
      <div className="px-4 py-3 border-t border-gray-700 text-xs text-gray-400">
        <p>💡 AI automatically matches tempo, key, and mix</p>
      </div>
    </div>
  )
}
