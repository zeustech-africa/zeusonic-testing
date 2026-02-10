'use client';

import { useState, useEffect, useRef } from 'react';
import WaveSurfer from 'wavesurfer.js';
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions';
import * as Tone from 'tone';
import { useAuth } from './auth/AuthProvider';
import { config } from '../lib/config';

interface AudioTrack {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  duration_seconds: number | null;
  status: string;
  created_at: string;
  stems?: Array<{ id: number; stem_type: string }>;
  analysis?: {
    bpm: number | null;
    musical_key: string | null;
    loudness_lufs: number | null;
    sample_rate: number | null;
    channels: number | null;
  };
}

interface AudioProcessorProps {
  projectId: number;
  projectName?: string;
}

interface TransformJob {
  id: number;
  track_id: number;
  source_style: string;
  target_style: string;
  status: string;
  output_path?: string | null;
  created_at: string;
  completed_at?: string | null;
}

const STYLE_OPTIONS = [
  { label: 'Reggae', value: 'reggae' },
  { label: 'Drill', value: 'drill' },
  { label: 'Acoustic', value: 'acoustic' },
  { label: 'Afrobeats', value: 'afrobeats' },
  { label: 'EDM', value: 'edm' },
  { label: 'Jazz', value: 'jazz' },
  { label: 'Amapiano', value: 'amapiano' },
  { label: 'House', value: 'house' },
  { label: 'HipHop', value: 'hiphop' },
] as const;
const MIXER_CONTROLS = [
  { label: 'Bass', key: 'bass' },
  { label: 'Treble', key: 'treble' },
  { label: 'Vocal presence', key: 'vocal_presence' },
  { label: 'Stereo width', key: 'stereo_width' },
] as const;
type MixerKey = (typeof MIXER_CONTROLS)[number]['key'];
const SUPPORTED_STYLE_VALUES = new Set(['amapiano', 'afrobeats', 'reggae', 'house', 'hiphop']);

export default function AudioProcessor({ projectId, projectName }: AudioProcessorProps) {
  const { token } = useAuth();
  const [tracks, setTracks] = useState<AudioTrack[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [transformJobs, setTransformJobs] = useState<Record<number, TransformJob | null>>({});
  const [transformStyles, setTransformStyles] = useState<Record<number, string>>({});
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [selectedTrackId, setSelectedTrackId] = useState<number | null>(null);
  const [mixerSettings, setMixerSettings] = useState<Record<number, { bass: number; treble: number; vocal_presence: number; stereo_width: number }>>({});
  const [styleSettings, setStyleSettings] = useState<Record<number, { intensity: number; preserveRhythm: boolean }>>({});
  const [instrumentSettings, setInstrumentSettings] = useState<Record<number, { mood: string; blend: number }>>({});
  const [lastExport, setLastExport] = useState<{ trackId: number; type: 'master' | 'mix' | 'transform' } | null>(null);
  const mixDebounceRef = useRef<Record<number, ReturnType<typeof setTimeout>>>({});
  const waveformContainerRef = useRef<HTMLDivElement | null>(null);
  const waveSurferRef = useRef<WaveSurfer | null>(null);
  const [waveformMode, setWaveformMode] = useState<'original' | 'transform' | 'mix' | 'master'>('original');
  const [waveZoom, setWaveZoom] = useState(60);
  const [waveformStatus, setWaveformStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [commandState, setCommandState] = useState<Record<number, { analyze?: boolean; splitStems?: boolean; transform?: boolean; mixAdjust?: boolean; instrument?: boolean; export?: boolean }>>({});
  const [pendingCapabilities, setPendingCapabilities] = useState<Record<number, { splitStems?: boolean; instrument?: boolean }>>({});
  const [transportPlaying, setTransportPlaying] = useState(false);
  const [transportPosition, setTransportPosition] = useState(0);
  const transportRafRef = useRef<number | null>(null);
  const [waveDuration, setWaveDuration] = useState(0);

  const fetchTracks = async () => {
    if (!token) return;

    try {
      const response = await fetch(`${config.apiUrl}/api/v1/projects/${projectId}/audio`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const nextTracks = data.tracks || [];
        setTracks(nextTracks);

        setTransformStyles((prev) => {
          const updated = { ...prev };
          nextTracks.forEach((track: AudioTrack) => {
            if (!updated[track.id]) {
              updated[track.id] = 'reggae';
            }
          });
          return updated;
        });

        await fetchTransformStatuses(nextTracks);

        if (nextTracks.length > 0 && selectedTrackId === null) {
          setSelectedTrackId(nextTracks[0].id);
        }

        setMixerSettings((prev) => {
          const updated = { ...prev };
          nextTracks.forEach((track: AudioTrack) => {
            if (!updated[track.id]) {
              updated[track.id] = { bass: 50, treble: 50, vocal_presence: 50, stereo_width: 50 };
            }
          });
          return updated;
        });

        setStyleSettings((prev) => {
          const updated = { ...prev };
          nextTracks.forEach((track: AudioTrack) => {
            if (!updated[track.id]) {
              updated[track.id] = { intensity: 60, preserveRhythm: true };
            }
          });
          return updated;
        });

        setInstrumentSettings((prev) => {
          const updated = { ...prev };
          nextTracks.forEach((track: AudioTrack) => {
            if (!updated[track.id]) {
              updated[track.id] = { mood: 'warm', blend: 60 };
            }
          });
          return updated;
        });
      }
    } catch (error) {
      console.error('Failed to fetch tracks:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransformStatuses = async (list: AudioTrack[]) => {
    if (!token || list.length === 0) return;
    try {
      const results = await Promise.all(
        list.map(async (track) => {
          const res = await fetch(`${config.apiUrl}/api/v1/audio/${track.id}/transform/status`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (!res.ok) {
            return { trackId: track.id, job: null };
          }
          const job = await res.json();
          return { trackId: track.id, job };
        })
      );

      setTransformJobs((prev) => {
        const updated = { ...prev };
        results.forEach(({ trackId, job }) => {
          updated[trackId] = job;
        });
        return updated;
      });
    } catch (error) {
      console.error('Failed to fetch transform status:', error);
    }
  };

  useEffect(() => {
    fetchTracks();
    const interval = setInterval(fetchTracks, 3000); // Poll every 3s
    return () => clearInterval(interval);
  }, [projectId, token]);

  const selectedTrack = selectedTrackId
    ? tracks.find((track) => track.id === selectedTrackId) || null
    : null;

  const currentMixer = selectedTrackId ? mixerSettings[selectedTrackId] : null;
  const currentStyle = selectedTrackId ? styleSettings[selectedTrackId] : null;
  const currentInstrument = selectedTrackId ? instrumentSettings[selectedTrackId] : null;

  const derivedTempo = selectedTrack?.analysis?.bpm
    ? `${selectedTrack.analysis.bpm.toFixed(1)} BPM`
    : '--';
  const derivedKey = selectedTrack?.analysis?.musical_key || '--';

  const setCommandStatus = (
    trackId: number,
    key: 'analyze' | 'splitStems' | 'transform' | 'mixAdjust' | 'instrument' | 'export',
    value: boolean
  ) => {
    setCommandState((prev) => ({
      ...prev,
      [trackId]: {
        ...prev[trackId],
        [key]: value,
      },
    }));
  };

  const postAiCommand = async (path: string, payload: Record<string, unknown>) => {
    if (!token) return null;
    try {
      const response = await fetch(`${config.apiUrl}/api/v1${path}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let detail = 'AI command failed.';
        try {
          const error = await response.json();
          detail = error.detail || detail;
        } catch (err) {
          if (response.status === 404) {
            detail = 'AI command endpoint not available.';
          }
        }
        setStatusMessage(detail);
        return null;
      }

      return await response.json();
    } catch (error) {
      console.error('AI command failed:', error);
      setStatusMessage('AI command failed. Please try again.');
      return null;
    }
  };

  const runAiCommand = async (
    trackId: number,
    key: 'analyze' | 'splitStems' | 'transform' | 'mixAdjust' | 'instrument' | 'export',
    path: string,
    payload: Record<string, unknown>
  ) => {
    setCommandStatus(trackId, key, true);
    const response = await postAiCommand(path, payload);
    setCommandStatus(trackId, key, false);
    return response;
  };

  const scheduleMixAdjust = (
    trackId: number,
    nextMixer: { bass: number; treble: number; vocal_presence: number; stereo_width: number }
  ) => {
    const timers = mixDebounceRef.current;
    if (timers[trackId]) {
      clearTimeout(timers[trackId]);
    }
    timers[trackId] = setTimeout(async () => {
      const response = await runAiCommand(trackId, 'mixAdjust', '/ai/mix-adjust', {
        track_id: trackId,
        bass: nextMixer.bass,
        treble: nextMixer.treble,
        vocals: nextMixer.vocal_presence,
      });
      if (response?.status === 'queued') {
        setStatusMessage('AI mix adjustment complete.');
        await fetchTracks();
      }
    }, 600);
  };

  const handleInstrumentAdd = async (instrument: string) => {
    if (!selectedTrackId) {
      setStatusMessage('Select a track before adding instruments.');
      return;
    }
    const response = await runAiCommand(selectedTrackId, 'instrument', '/ai/add-instrument', {
      track_id: selectedTrackId,
      instrument: instrument.toLowerCase(),
      intensity: currentInstrument?.blend ?? 60,
    });
    if (response?.ai_engine_pending) {
      setPendingCapabilities((prev) => ({
        ...prev,
        [selectedTrackId]: { ...prev[selectedTrackId], instrument: true },
      }));
      setStatusMessage('AI Engine connected — execution coming next');
      return;
    }
    if (response?.status === 'queued') {
      setStatusMessage(`AI instrument layer queued: ${instrument}.`);
    }
  };

  const handleSplitStems = async (trackId: number) => {
    const response = await runAiCommand(trackId, 'splitStems', '/ai/separate', {
      track_id: trackId,
    });
    if (response?.ai_engine_pending) {
      setPendingCapabilities((prev) => ({
        ...prev,
        [trackId]: { ...prev[trackId], splitStems: true },
      }));
      setStatusMessage('AI Engine connected — execution coming next');
      return;
    }
    if (response?.status === 'queued') {
      setStatusMessage('Stem separation queued.');
      await fetchTracks();
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !token) return;

    setUploading(true);
    setStatusMessage('Uploading audio...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${config.apiUrl}/api/v1/projects/${projectId}/audio`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        await fetchTracks();
        setStatusMessage('Upload complete. Analyzing audio...');
        if (data?.id) {
          await runAiCommand(data.id, 'analyze', '/ai/analyze', {
            track_id: data.id,
          });
        }
      } else {
        const error = await response.json();
        setStatusMessage(`Upload failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setStatusMessage('Upload failed. Please try again.');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const triggerMix = async (trackId: number) => {
    if (!token) return;

    try {
      const response = await fetch(`${config.apiUrl}/api/v1/audio/${trackId}/mix`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchTracks();
        setStatusMessage('Mix job started. This may take a moment.');
      } else {
        const error = await response.json();
        setStatusMessage(`Mix failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Mix failed:', error);
      setStatusMessage('Mix failed. Please try again.');
    }
  };

  const triggerMaster = async (trackId: number) => {
    if (!token) return;

    try {
      const response = await fetch(`${config.apiUrl}/api/v1/audio/${trackId}/master`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchTracks();
        setStatusMessage('Master job started. This may take a moment.');
      } else {
        const error = await response.json();
        setStatusMessage(`Master failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Master failed:', error);
      setStatusMessage('Master failed. Please try again.');
    }
  };

  const downloadWithAuth = async (url: string, fallbackName: string) => {
    if (!token) return;
    try {
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error('Download failed');
      }
      const blob = await response.blob();
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = fallbackName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setStatusMessage('Download started.');
    } catch (error) {
      console.error('Download failed:', error);
      setStatusMessage('Download failed. Please try again.');
    }
  };

  const downloadProcessed = (trackId: number, processType: 'mix' | 'master') => {
    const url = `${config.apiUrl}/api/v1/audio/download/${trackId}/${processType}`;
    downloadWithAuth(url, `track_${trackId}_${processType}.wav`);
  };

  const downloadTransform = (trackId: number) => {
    const url = `${config.apiUrl}/api/v1/audio/${trackId}/transform/download`;
    downloadWithAuth(url, `track_${trackId}_transform.wav`);
  };

  const handleExport = () => {
    if (!selectedTrackId) {
      setStatusMessage('Select a track before exporting.');
      return;
    }
    runAiCommand(selectedTrackId, 'export', '/ai/export', {
      track_id: selectedTrackId,
    }).then((response) => {
      if (!response) return;
      if (response.ai_engine_pending) {
        setStatusMessage('AI Engine connected — execution coming next');
        return;
      }
      if (response.download_url) {
        const downloadUrl = `${config.apiUrl}${response.download_url}`;
        if (response.download_url.includes('/master')) {
          setLastExport({ trackId: selectedTrackId, type: 'master' });
        } else if (response.download_url.includes('/mix')) {
          setLastExport({ trackId: selectedTrackId, type: 'mix' });
        } else {
          setLastExport({ trackId: selectedTrackId, type: 'transform' });
        }
        downloadWithAuth(downloadUrl, `track_${selectedTrackId}_export.wav`);
      } else {
        setStatusMessage(response.detail || 'Export queued.');
      }
    });
  };

  const handleExportDownload = () => {
    if (!lastExport) return;
    if (lastExport.type === 'transform') {
      downloadTransform(lastExport.trackId);
      return;
    }
    downloadProcessed(lastExport.trackId, lastExport.type);
  };

  const triggerTransform = async (trackId: number) => {
    const targetStyle = transformStyles[trackId] || 'reggae';
    const style = styleSettings[trackId];
    const response = await runAiCommand(trackId, 'transform', '/ai/style-transfer', {
      track_id: trackId,
      style: targetStyle,
      reference_audio: null,
    });
    if (response?.status === 'queued') {
      await fetchTracks();
      setStatusMessage('AI transform queued. Watch status for completion.');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return '--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'uploaded':
      case 'analyzing':
        return 'text-yellow-400';
      case 'analyzed':
      case 'mixed':
      case 'mastered':
        return 'text-green-400';
      case 'mixing':
      case 'mastering':
        return 'text-blue-400';
      case 'failed':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const getTransformStatusColor = (status: string): string => {
    switch (status) {
      case 'pending':
      case 'processing':
        return 'text-blue-400';
      case 'completed':
        return 'text-green-400';
      case 'failed':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const transformReady = selectedTrackId
    ? transformJobs[selectedTrackId]?.status === 'completed'
    : false;
  const mixReady = selectedTrack?.status === 'mixed' || selectedTrack?.status === 'mastered';
  const masterReady = selectedTrack?.status === 'mastered';
  const exportReady = transformReady || mixReady || masterReady;

  useEffect(() => {
    if (!selectedTrackId) return;
    if (waveformMode === 'master' && !masterReady) {
      setWaveformMode('original');
    } else if (waveformMode === 'mix' && !mixReady) {
      setWaveformMode('original');
    } else if (waveformMode === 'transform' && !transformReady) {
      setWaveformMode('original');
    }
  }, [selectedTrackId, transformReady, mixReady, masterReady, waveformMode]);

  useEffect(() => {
    if (!waveformContainerRef.current) return;
    if (waveSurferRef.current) {
      waveSurferRef.current.destroy();
    }

    const ws = WaveSurfer.create({
      container: waveformContainerRef.current,
      waveColor: '#6d28d9',
      progressColor: '#ec4899',
      cursorColor: '#f9fafb',
      barWidth: 2,
      barGap: 2,
      height: 120,
      normalize: true,
      plugins: [RegionsPlugin.create()],
    });

    waveSurferRef.current = ws;

    return () => {
      ws.destroy();
    };
  }, []);

  useEffect(() => {
    if (!selectedTrackId && waveSurferRef.current) {
      const ws = waveSurferRef.current as unknown as { empty?: () => void };
      ws.empty?.();
      setWaveformStatus('idle');
    }
  }, [selectedTrackId]);

  useEffect(() => {
    const ws = waveSurferRef.current;
    if (!ws || !token || !selectedTrackId) return;

    const getWaveformUrl = () => {
      if (waveformMode === 'master') {
        return `${config.apiUrl}/api/v1/audio/download/${selectedTrackId}/master`;
      }
      if (waveformMode === 'mix') {
        return `${config.apiUrl}/api/v1/audio/download/${selectedTrackId}/mix`;
      }
      if (waveformMode === 'transform') {
        return `${config.apiUrl}/api/v1/audio/${selectedTrackId}/transform/download`;
      }
      return `${config.apiUrl}/api/v1/audio/${selectedTrackId}/source/download`;
    };

    const url = getWaveformUrl();
    setWaveformStatus('loading');

    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Waveform fetch failed');
        }
        return response.blob();
      })
      .then((blob) => {
        ws.loadBlob(blob);
        ws.once('ready', () => {
          ws.zoom(waveZoom);
          const duration = ws.getDuration();
          const regionApi = ws as unknown as { clearRegions?: () => void; addRegion?: (opts: any) => void };
          if (regionApi.clearRegions) {
            regionApi.clearRegions();
          }
          if (regionApi.addRegion && duration > 0) {
            const sections = [
              { label: 'Intro', start: 0, end: duration * 0.18, color: 'rgba(88, 101, 242, 0.18)' },
              { label: 'Drop', start: duration * 0.18, end: duration * 0.45, color: 'rgba(236, 72, 153, 0.18)' },
              { label: 'Chorus', start: duration * 0.45, end: duration * 0.72, color: 'rgba(16, 185, 129, 0.18)' },
              { label: 'Outro', start: duration * 0.72, end: duration * 0.98, color: 'rgba(148, 163, 184, 0.18)' },
            ];
            sections.forEach((section) => {
              regionApi.addRegion?.({
                start: section.start,
                end: section.end,
                color: section.color,
                drag: false,
                resize: false,
              });
            });
          }
          setWaveformStatus('ready');
          setTransportPosition(0);
          Tone.Transport.seconds = 0;
        });
      })
      .catch((error) => {
        console.error('Waveform load failed:', error);
        setWaveformStatus('error');
        setStatusMessage('Waveform preview unavailable.');
      });
  }, [selectedTrackId, waveformMode, token]);

  useEffect(() => {
    if (waveSurferRef.current) {
      waveSurferRef.current.zoom(waveZoom);
    }
  }, [waveZoom]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 rounded-lg border border-purple-500/20 bg-black/40 px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs text-muted">Session</div>
            <div className="text-lg font-semibold text-white">{projectName || 'Studio Session'}</div>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-400">
            <span>Tempo: {derivedTempo}</span>
            <span>Key: {derivedKey}</span>
            <span className="text-muted">AI‑assisted</span>
          </div>
          <div className="flex items-center gap-2 text-[11px]">
            {(selectedTrack?.status === 'analyzing' || selectedTrack?.status === 'mixing' || selectedTrack?.status === 'mastering') && (
              <span className="px-2 py-1 rounded-full bg-blue-500/20 text-blue-200">Processing</span>
            )}
            {(transformReady || mixReady || masterReady) && (
              <span className="px-2 py-1 rounded-full bg-green-500/20 text-green-200">New version ready</span>
            )}
            {exportReady && (
              <span className="px-2 py-1 rounded-full bg-purple-500/20 text-purple-200">Export available</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              className="px-3 py-2 rounded bg-black/60 border border-white/10 text-sm text-muted cursor-not-allowed"
            >
              Play
            </button>
            <button
              className="px-3 py-2 rounded bg-black/60 border border-white/10 text-sm text-muted cursor-not-allowed"
            >
              Stop
            </button>
            <button
              onClick={handleExport}
              disabled={selectedTrackId ? commandState[selectedTrackId]?.export : false}
              className="px-4 py-2 rounded bg-purple-600 hover:bg-purple-700 text-sm text-white transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Render Export
            </button>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted">
          <span>{statusMessage || 'AI standing by — import a track to begin.'}</span>
          {lastExport && (
            <button
              onClick={handleExportDownload}
              className="text-xs text-purple-300 underline hover:text-purple-200"
            >
              Bounce last export
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left: Track List */}
        <div className="lg:col-span-3 space-y-4">
          <div className="p-4 bg-black/30 rounded-lg border border-purple-500/20">
            <div className="text-xs text-muted">Project</div>
            <div className="text-lg font-semibold text-white">{projectName || 'Studio Session'}</div>
            <div className="mt-2 text-sm text-gray-400">Tempo: {derivedTempo}</div>
            <div className="text-sm text-gray-400">Key: {derivedKey}</div>
          </div>

          <div className="p-4 bg-black/30 rounded-lg border border-purple-500/20">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-semibold text-white">Stems + Layers</div>
              <span className="text-xs text-muted">{tracks.length}</span>
            </div>
            {loading ? (
              <div className="text-sm text-gray-400">Loading tracks...</div>
            ) : tracks.length === 0 ? (
              <div className="text-sm text-gray-400">No stems yet.</div>
            ) : (
              <div className="space-y-2">
                {tracks.map((track) => (
                  <button
                    key={track.id}
                    onClick={() => setSelectedTrackId(track.id)}
                    className={`w-full text-left rounded px-3 py-2 border transition ${
                      selectedTrackId === track.id
                        ? 'border-purple-500 bg-purple-500/10'
                        : 'border-white/10 bg-black/40 hover:border-purple-500/40'
                    }`}
                  >
                    <div className="text-sm text-white font-medium truncate">{track.original_filename}</div>
                    <div className="studio-meter" aria-hidden="true">
                      <span className="studio-meter-bar" />
                      <span className="studio-meter-bar" />
                      <span className="studio-meter-bar" />
                      <span className="studio-meter-bar" />
                      <span className="studio-meter-bar" />
                    </div>
                    <div className="text-xs text-gray-400 flex items-center gap-2">
                      <span>{formatDuration(track.duration_seconds)}</span>
                      <span>•</span>
                      <span className={getStatusColor(track.status)}>{track.status}</span>
                      {commandState[track.id]?.analyze && (
                        <span className="text-[10px] text-blue-300">AI analysis</span>
                      )}
                      {commandState[track.id]?.mixAdjust && (
                        <span className="text-[10px] text-blue-300">AI mix adjust</span>
                      )}
                      {commandState[track.id]?.instrument && (
                        <span className="text-[10px] text-purple-300">AI layer</span>
                      )}
                      {transformJobs[track.id]?.status && (
                        <span className={`text-[10px] ${getTransformStatusColor(transformJobs[track.id]?.status || '')}`}>
                          transform {transformJobs[track.id]?.status}
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="p-4 bg-black/30 rounded-lg border border-purple-500/20">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-semibold text-white">Stem Control Panel</div>
              {selectedTrack && (
                <button
                  onClick={() => handleSplitStems(selectedTrack.id)}
                  disabled={commandState[selectedTrack.id]?.splitStems || pendingCapabilities[selectedTrack.id]?.splitStems}
                  title={pendingCapabilities[selectedTrack.id]?.splitStems ? 'AI Engine connected — execution coming next' : undefined}
                  className="text-xs px-2 py-1 rounded bg-black/60 border border-white/10 text-muted hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Split stems
                </button>
              )}
            </div>
            <div className="space-y-2 text-xs text-gray-400">
              {selectedTrack ? (
                (selectedTrack.stems && selectedTrack.stems.length > 0) ? (
                  selectedTrack.stems.map((stem) => (
                    <div key={stem.id} className="flex items-center justify-between gap-2">
                      <span className="text-gray-300 capitalize">{stem.stem_type.replace('_', ' ')}</span>
                      <div className="flex gap-2">
                        <button className="px-2 py-1 rounded bg-black/60 border border-white/10 cursor-not-allowed">Mute</button>
                        <button className="px-2 py-1 rounded bg-black/60 border border-white/10 cursor-not-allowed">Solo</button>
                        <button className="px-2 py-1 rounded bg-black/60 border border-white/10 cursor-not-allowed">Vol</button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-muted">No stems yet. Split stems to populate lanes.</div>
                )
              ) : (
                <div className="text-xs text-muted">Select a track to manage stems.</div>
              )}
            </div>
            <div className="mt-2 text-xs text-muted">
              AI Engine connected — execution coming next.
            </div>
          </div>
        </div>

        {/* Center: Timeline + Upload */}
        <div className="lg:col-span-6 space-y-4">
          <div className="p-4 bg-black/30 rounded-lg border border-purple-500/20">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-semibold text-white">Arrangement</div>
              <div className="text-xs text-muted">Session view</div>
            </div>
            <div className="mb-3 rounded bg-black/40 border border-white/5 px-3 py-2 text-[10px] text-muted">
              {/* UI-only (future backend hook): section markers */}
              Section markers: Intro • Drop • Chorus • Outro
            </div>
            {!selectedTrack ? (
              <div className="h-36 rounded bg-black/50 border border-white/5 flex items-center justify-center text-muted">
                Import a track to see your waveform here.
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="w-24 text-xs text-gray-400 truncate">Original</div>
                  <div className="flex-1 h-6 rounded bg-purple-500/10 border border-purple-500/30 relative overflow-hidden">
                    <div
                      className="absolute inset-y-0 left-0 bg-purple-500/40"
                      style={{ width: `${Math.min(100, Math.max(20, (selectedTrack.duration_seconds || 30) * 2))}%` }}
                    />
                  </div>
                  {selectedTrack.status === 'analyzing' && (
                    <span className="text-[10px] text-blue-400">Analyzing stems...</span>
                  )}
                </div>
                {(selectedTrack.stems && selectedTrack.stems.length > 0) && (
                  <div className="space-y-2">
                    {selectedTrack.stems.map((stem) => (
                      <div key={stem.id} className="flex items-center gap-2">
                        <div className="w-24 text-xs text-gray-400 truncate capitalize">
                          {stem.stem_type.replace('_', ' ')}
                        </div>
                        <div className="flex-1 h-5 rounded bg-blue-500/10 border border-blue-500/30 relative overflow-hidden">
                          <div className="absolute inset-y-0 left-0 bg-blue-500/40" style={{ width: '70%' }} />
                        </div>
                        <span className="text-[10px] text-muted">Read-only stem</span>
                      </div>
                    ))}
                  </div>
                )}
                {(!selectedTrack.stems || selectedTrack.stems.length === 0) && pendingCapabilities[selectedTrack.id]?.splitStems && (
                  <div className="space-y-2">
                    {['Vocals', 'Instrumental', 'AI-generated'].map((label) => (
                      <div key={label} className="flex items-center gap-2">
                        <div className="w-24 text-xs text-gray-400 truncate">{label}</div>
                        <div className="flex-1 h-5 rounded bg-black/40 border border-white/10" />
                        <span className="text-[10px] text-muted">AI Engine connected — execution coming next</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="p-4 bg-black/30 rounded-lg border border-purple-500/20">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
              <div>
                <div className="text-sm font-semibold text-white">Waveform</div>
                <div className="text-xs text-muted">Active render: {waveformMode}</div>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <label className="text-muted">Output</label>
                <select
                  value={waveformMode}
                  onChange={(e) => setWaveformMode(e.target.value as typeof waveformMode)}
                  className="px-2 py-1 rounded bg-black/60 border border-white/10 text-white"
                >
                  <option value="original">Original</option>
                  {transformReady && <option value="transform">Transform</option>}
                  {mixReady && <option value="mix">Mix</option>}
                  {masterReady && <option value="master">Master</option>}
                </select>
                <label className="text-muted">Zoom</label>
                <input
                  type="range"
                  min={20}
                  max={200}
                  value={waveZoom}
                  onChange={(e) => setWaveZoom(Number(e.target.value))}
                  className="studio-knob w-28"
                />
              </div>
            </div>
            <div className="rounded bg-black/50 border border-white/5 p-3">
              <div ref={waveformContainerRef} className="w-full" />
              <div className="mt-2 text-xs text-muted">
                {waveformStatus === 'loading' && 'Rendering waveform...'}
                {waveformStatus === 'ready' && 'Waveform ready — AI-assisted render preview.'}
                {waveformStatus === 'error' && 'Waveform unavailable — try another output.'}
                {waveformStatus === 'idle' && 'Waveform ready when a track is selected.'}
              </div>
            </div>
          </div>

          <div className="p-6 bg-black/30 rounded-lg border border-purple-500/20">
            <h3 className="text-lg font-bold text-white mb-4">Upload Track</h3>
            <div className="flex items-center gap-4">
              <label className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg cursor-pointer hover:opacity-90 transition-opacity">
                {uploading ? 'Uploading...' : 'Import Track'}
                <input
                  type="file"
                  accept=".wav,.mp3"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="hidden"
                />
              </label>
              <p className="text-sm text-gray-400">Supports WAV + MP3 (max 100 MB)</p>
            </div>
            {statusMessage && (
              <div className="mt-3 text-sm text-muted">{statusMessage}</div>
            )}
          </div>
        </div>

        {/* Right: AI Controls */}
        <div className="lg:col-span-3 space-y-4">
          <div className="p-4 bg-black/30 rounded-lg border border-purple-500/20">
            <div className="text-sm font-semibold text-white mb-3">AI‑assisted mix</div>
            {/* AI-assisted control (AI command wired) */}
            {selectedTrack ? (
              <div className="space-y-3 text-xs text-gray-400">
                {MIXER_CONTROLS.map(({ label, key }) => (
                  <div key={label}>
                    <div className="flex items-center justify-between">
                      <span>{label}</span>
                      <span className="text-muted">AI‑driven</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      value={currentMixer ? currentMixer[key as MixerKey] : 50}
                      onChange={(e) => {
                        if (!selectedTrackId) return;
                        const value = Number(e.target.value);
                        setMixerSettings((prev) => {
                          const next = {
                            ...prev,
                            [selectedTrackId]: {
                              ...prev[selectedTrackId],
                              [key]: value,
                            },
                          };
                          scheduleMixAdjust(selectedTrackId, next[selectedTrackId]);
                          return next;
                        });
                        setStatusMessage(`AI adjusting ${label.toLowerCase()}...`);
                      }}
                      className="w-full studio-knob"
                      disabled={selectedTrackId ? commandState[selectedTrackId]?.mixAdjust : false}
                    />
                  </div>
                ))}
                <div className="text-xs text-muted">
                  AI-assisted controls (AI command wired).
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-400">Select a track to view controls.</div>
            )}
          </div>

          <div className="p-4 bg-black/30 rounded-lg border border-purple-500/20">
            <div className="text-sm font-semibold text-white mb-3">Style Transform</div>
            {/* AI-assisted control (AI command wired) */}
            {selectedTrack ? (
              <div className="space-y-3">
                <label className="text-xs text-gray-400">Style</label>
                <select
                  value={transformStyles[selectedTrack.id] || 'reggae'}
                  onChange={(e) =>
                    setTransformStyles((prev) => {
                      const value = e.target.value;
                      if (SUPPORTED_STYLE_VALUES.has(value)) {
                        setPendingCapabilities((pending) => ({
                          ...pending,
                          [selectedTrack.id]: { ...pending[selectedTrack.id], transform: false },
                        }));
                      }
                      return {
                        ...prev,
                        [selectedTrack.id]: value,
                      };
                    })
                  }
                  className="w-full px-3 py-2 bg-black/60 border border-purple-500/30 rounded-lg text-white text-sm"
                  disabled={selectedTrackId ? commandState[selectedTrackId]?.transform : false}
                >
                  {STYLE_OPTIONS.map((style) => (
                    <option key={style.value} value={style.value}>
                      {style.label}
                    </option>
                  ))}
                </select>
                <label className="text-xs text-gray-400">Intensity</label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={currentStyle?.intensity ?? 60}
                  onChange={(e) => {
                    if (!selectedTrackId) return;
                    setStyleSettings((prev) => ({
                      ...prev,
                      [selectedTrackId]: {
                        ...prev[selectedTrackId],
                        intensity: Number(e.target.value),
                      },
                    }));
                  }}
                  className="w-full studio-knob"
                  disabled={selectedTrackId ? commandState[selectedTrackId]?.transform : false}
                />
                <label className="flex items-center gap-2 text-xs text-gray-400">
                  <input
                    type="checkbox"
                    checked={currentStyle?.preserveRhythm ?? true}
                    onChange={(e) => {
                      if (!selectedTrackId) return;
                      setStyleSettings((prev) => ({
                        ...prev,
                        [selectedTrackId]: {
                          ...prev[selectedTrackId],
                          preserveRhythm: e.target.checked,
                        },
                      }));
                    }}
                    className="accent-purple-500"
                    disabled={selectedTrackId ? commandState[selectedTrackId]?.transform : false}
                  />
                  Preserve rhythm
                </label>
                <button
                  onClick={() => triggerTransform(selectedTrack.id)}
                  disabled={transformJobs[selectedTrack.id]?.status === 'processing' || commandState[selectedTrack.id]?.transform}
                  className="w-full px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                >
                  {transformJobs[selectedTrack.id]?.status === 'processing' || commandState[selectedTrack.id]?.transform ? 'Rendering...' : 'Render Style'}
                </button>
                {transformJobs[selectedTrack.id]?.status && (
                  <div className={`text-xs ${getTransformStatusColor(transformJobs[selectedTrack.id]?.status || '')}`}>
                    {transformJobs[selectedTrack.id]?.status}
                  </div>
                )}
                <div className="text-xs text-muted">AI-assisted controls (AI command wired).</div>
                {transformJobs[selectedTrack.id]?.status === 'completed' && (
                  <button
                    onClick={() => downloadTransform(selectedTrack.id)}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                  >
                    Bounce Transform
                  </button>
                )}
              </div>
            ) : (
              <div className="text-sm text-gray-400">Select a track to transform.</div>
            )}
          </div>

          <div className="p-4 bg-black/30 rounded-lg border border-purple-500/20">
            <div className="text-sm font-semibold text-white mb-3">Instrument Add</div>
            <div className="text-xs text-gray-400 space-y-3">
              {/* AI-assisted control (AI command wired) */}
              <div className="text-muted">AI-generated instrument layer (read-only).</div>
              <label className="text-xs text-gray-400">Mood</label>
              <select
                value={currentInstrument?.mood || 'warm'}
                onChange={(e) => {
                  if (!selectedTrackId) return;
                  setInstrumentSettings((prev) => ({
                    ...prev,
                    [selectedTrackId]: {
                      ...prev[selectedTrackId],
                      mood: e.target.value,
                    },
                  }));
                }}
                className="w-full px-3 py-2 bg-black/60 border border-purple-500/30 rounded-lg text-white text-sm"
                disabled={selectedTrackId ? commandState[selectedTrackId]?.instrument : false}
              >
                {['Warm', 'Dark', 'Bright', 'Aggressive'].map((mood) => (
                  <option key={mood} value={mood.toLowerCase()}>{mood}</option>
                ))}
              </select>
              <label className="text-xs text-gray-400">Blend</label>
              <input
                type="range"
                min={0}
                max={100}
                value={currentInstrument?.blend ?? 60}
                onChange={(e) => {
                  if (!selectedTrackId) return;
                  setInstrumentSettings((prev) => ({
                    ...prev,
                    [selectedTrackId]: {
                      ...prev[selectedTrackId],
                      blend: Number(e.target.value),
                    },
                  }));
                }}
                className="w-full studio-knob"
                disabled={selectedTrackId ? commandState[selectedTrackId]?.instrument : false}
              />
              <div className="grid grid-cols-2 gap-2">
                {['Bass', 'Guitar', 'Piano', 'Strings', 'Percussion', 'Synth'].map((instrument) => (
                  <button
                    key={instrument}
                    onClick={() => handleInstrumentAdd(instrument)}
                    disabled={selectedTrackId ? commandState[selectedTrackId]?.instrument || pendingCapabilities[selectedTrackId]?.instrument : false}
                    title={pendingCapabilities[selectedTrackId]?.instrument ? 'AI Engine connected — execution coming next' : undefined}
                    className="px-3 py-2 rounded bg-black/60 border border-white/10 hover:border-purple-400/60 hover:text-white transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {instrument}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {selectedTrack && (
            <div className="p-4 bg-black/30 rounded-lg border border-purple-500/20">
              <div className="text-sm font-semibold text-white mb-3">Render & Bounce</div>
              <div className="flex flex-col gap-2">
                <button
                  onClick={() => triggerMix(selectedTrack.id)}
                  disabled={selectedTrack.status === 'mixing' || commandState[selectedTrack.id]?.mixAdjust}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                >
                  {selectedTrack.status === 'mixing' ? 'Rendering Mix...' : 'Render Mix'}
                </button>
                <button
                  onClick={() => triggerMaster(selectedTrack.id)}
                  disabled={selectedTrack.status === 'mastering' || commandState[selectedTrack.id]?.export}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                >
                  {selectedTrack.status === 'mastering' ? 'Rendering Master...' : 'Render Master'}
                </button>
                {selectedTrack.status === 'mixed' || selectedTrack.status === 'mastered' ? (
                  <button
                    onClick={() => downloadProcessed(selectedTrack.id, 'mix')}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                  >
                    Bounce Mix
                  </button>
                ) : null}
                {selectedTrack.status === 'mastered' && (
                  <button
                    onClick={() => downloadProcessed(selectedTrack.id, 'master')}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                  >
                    Bounce Master
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {selectedTrack?.status === 'failed' && (
        <div className="p-3 bg-red-900/20 border border-red-500/30 rounded text-red-400 text-sm">
          Render failed. Please try re-importing or contact support.
        </div>
      )}
    </div>
  );
}
