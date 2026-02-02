'use client';

import { useState, useEffect } from 'react';
import { useAuth } from './auth/AuthProvider';

interface AudioTrack {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  duration_seconds: number | null;
  status: string;
  created_at: string;
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

const STYLE_OPTIONS = ['amapiano', 'afrobeats', 'reggae', 'house', 'hiphop'] as const;

export default function AudioProcessor({ projectId }: AudioProcessorProps) {
  const { token } = useAuth();
  const [tracks, setTracks] = useState<AudioTrack[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [transformJobs, setTransformJobs] = useState<Record<number, TransformJob | null>>({});
  const [transformStyles, setTransformStyles] = useState<Record<number, string>>({});

  const fetchTracks = async () => {
    if (!token) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/audio`, {
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
              updated[track.id] = 'amapiano';
            }
          });
          return updated;
        });

        await fetchTransformStatuses(nextTracks);
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
          const res = await fetch(`http://localhost:8000/api/v1/audio/${track.id}/transform/status`, {
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

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !token) return;

    setUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/audio`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        await fetchTracks();
      } else {
        const error = await response.json();
        alert(`Upload failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const triggerMix = async (trackId: number) => {
    if (!token) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/audio/${trackId}/mix`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchTracks();
      } else {
        const error = await response.json();
        alert(`Mix failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Mix failed:', error);
    }
  };

  const triggerMaster = async (trackId: number) => {
    if (!token) return;

    try {
      const response = await fetch(`http://localhost:8000/api/v1/audio/${trackId}/master`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await fetchTracks();
      } else {
        const error = await response.json();
        alert(`Master failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Master failed:', error);
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
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
  };

  const downloadProcessed = (trackId: number, processType: 'mix' | 'master') => {
    const url = `http://localhost:8000/api/v1/audio/download/${trackId}/${processType}`;
    downloadWithAuth(url, `track_${trackId}_${processType}.wav`);
  };

  const downloadTransform = (trackId: number) => {
    const url = `http://localhost:8000/api/v1/audio/${trackId}/transform/download`;
    downloadWithAuth(url, `track_${trackId}_transform.wav`);
  };

  const triggerTransform = async (trackId: number) => {
    if (!token) return;
    const targetStyle = transformStyles[trackId] || 'amapiano';
    try {
      const response = await fetch(`http://localhost:8000/api/v1/audio/${trackId}/transform`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ target_style: targetStyle }),
      });

      if (response.ok) {
        await fetchTracks();
      } else {
        const error = await response.json();
        alert(`Transform failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Transform failed:', error);
      alert('Transform failed. Please try again.');
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

  if (loading) {
    return (
      <div className="p-6 bg-black/30 rounded-lg border border-purple-500/20">
        <p className="text-gray-400">Loading audio tracks...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="p-6 bg-black/30 rounded-lg border border-purple-500/20">
        <h3 className="text-lg font-bold text-white mb-4">Upload Audio</h3>
        <div className="flex items-center gap-4">
          <label className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg cursor-pointer hover:opacity-90 transition-opacity">
            {uploading ? 'Uploading...' : 'Choose File'}
            <input
              type="file"
              accept=".wav,.mp3"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
          <p className="text-sm text-gray-400">Supports WAV and MP3 (max 100 MB)</p>
        </div>
      </div>

      {/* Tracks List */}
      {tracks.length === 0 ? (
        <div className="p-6 bg-black/30 rounded-lg border border-purple-500/20 text-center">
          <p className="text-gray-400">No audio tracks uploaded yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {tracks.map((track) => (
            <div
              key={track.id}
              className="p-6 bg-black/30 rounded-lg border border-purple-500/20 hover:border-purple-500/40 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h4 className="text-white font-semibold">{track.original_filename}</h4>
                  <div className="flex items-center gap-4 mt-1 text-sm text-gray-400">
                    <span>{formatFileSize(track.file_size)}</span>
                    <span>•</span>
                    <span>{formatDuration(track.duration_seconds)}</span>
                    <span>•</span>
                    <span className={getStatusColor(track.status)}>{track.status}</span>
                  </div>
                </div>
              </div>

              {/* Analysis Results */}
              {track.analysis && (
                <div className="mb-4 p-4 bg-black/50 rounded-lg">
                  <h5 className="text-white font-semibold mb-2">Analysis</h5>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                    <div>
                      <p className="text-gray-400">BPM</p>
                      <p className="text-white font-mono">
                        {track.analysis.bpm ? track.analysis.bpm.toFixed(1) : '--'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">Key</p>
                      <p className="text-white font-mono">
                        {track.analysis.musical_key || '--'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">LUFS</p>
                      <p className="text-white font-mono">
                        {track.analysis.loudness_lufs
                          ? track.analysis.loudness_lufs.toFixed(1)
                          : '--'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">Sample Rate</p>
                      <p className="text-white font-mono">
                        {track.analysis.sample_rate
                          ? `${(track.analysis.sample_rate / 1000).toFixed(1)}kHz`
                          : '--'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">Channels</p>
                      <p className="text-white font-mono">
                        {track.analysis.channels || '--'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              {track.status === 'analyzed' || track.status === 'mixed' || track.status === 'mastered' ? (
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => triggerMix(track.id)}
                    disabled={track.status === 'mixing'}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                  >
                    {track.status === 'mixing' ? 'Mixing...' : 'Run Mix'}
                  </button>
                  <button
                    onClick={() => triggerMaster(track.id)}
                    disabled={track.status === 'mastering'}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                  >
                    {track.status === 'mastering' ? 'Mastering...' : 'Run Master'}
                  </button>
                  {track.status === 'mixed' || track.status === 'mastered' ? (
                    <>
                      <button
                        onClick={() => downloadProcessed(track.id, 'mix')}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                      >
                        Download Mix
                      </button>
                      {track.status === 'mastered' && (
                        <button
                          onClick={() => downloadProcessed(track.id, 'master')}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                        >
                          Download Master
                        </button>
                      )}
                    </>
                  ) : null}
                </div>
              ) : null}

              {/* Beat Transformation */}
              {track.status === 'analyzed' || track.status === 'mixed' || track.status === 'mastered' ? (
                <div className="mt-4 p-4 bg-black/50 rounded-lg">
                  <div className="flex flex-wrap items-center gap-3">
                    <label className="text-sm text-gray-400">Style</label>
                    <select
                      value={transformStyles[track.id] || 'amapiano'}
                      onChange={(e) =>
                        setTransformStyles((prev) => ({
                          ...prev,
                          [track.id]: e.target.value,
                        }))
                      }
                      className="px-3 py-2 bg-black/60 border border-purple-500/30 rounded-lg text-white text-sm"
                    >
                      {STYLE_OPTIONS.map((style) => (
                        <option key={style} value={style}>
                          {style}
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={() => triggerTransform(track.id)}
                      disabled={transformJobs[track.id]?.status === 'processing'}
                      className="px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                    >
                      {transformJobs[track.id]?.status === 'processing' ? 'Transforming...' : 'Transform Beat'}
                    </button>
                    {transformJobs[track.id]?.status && (
                      <span className={`text-sm ${getTransformStatusColor(transformJobs[track.id]?.status || '')}`}>
                        {transformJobs[track.id]?.status}
                      </span>
                    )}
                    {transformJobs[track.id]?.status === 'completed' && (
                      <button
                        onClick={() => downloadTransform(track.id)}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                      >
                        Download Transform
                      </button>
                    )}
                  </div>
                  <p className="mt-2 text-xs text-gray-500">
                    Beat transformation preserves harmony and melody while re-grooving the rhythm.
                  </p>
                </div>
              ) : null}

              {track.status === 'failed' && (
                <div className="mt-2 p-3 bg-red-900/20 border border-red-500/30 rounded text-red-400 text-sm">
                  Processing failed. Please try re-uploading or contact support.
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
