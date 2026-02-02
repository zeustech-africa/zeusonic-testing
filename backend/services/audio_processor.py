"""Audio processing utilities for analysis, mixing, and mastering."""
import librosa
import numpy as np
import pyloudnorm as pyln
from pydub import AudioSegment
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


def analyze_audio(file_path: Path) -> Dict[str, Any]:
    """Analyze audio file and return metadata."""
    try:
        # Load audio with librosa
        y, sr = librosa.load(str(file_path), sr=None, mono=False)
        
        # Handle stereo vs mono
        if y.ndim > 1:
            y_mono = librosa.to_mono(y)
            channels = y.shape[0]
        else:
            y_mono = y
            channels = 1
        
        # Duration
        duration = librosa.get_duration(y=y_mono, sr=sr)
        
        # BPM detection
        try:
            tempo, _ = librosa.beat.beat_track(y=y_mono, sr=sr)
            bpm = float(tempo)
        except:
            bpm = None
        
        # Key detection (simplified using chroma)
        try:
            chroma = librosa.feature.chroma_cqt(y=y_mono, sr=sr)
            key_index = np.argmax(np.sum(chroma, axis=1))
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            musical_key = keys[key_index]
        except:
            musical_key = None
        
        # Loudness (LUFS) - using pyloudnorm
        try:
            meter = pyln.Meter(sr)
            if y.ndim > 1:
                loudness = meter.integrated_loudness(y.T)
            else:
                loudness = meter.integrated_loudness(y.reshape(-1, 1))
        except:
            loudness = None
        
        return {
            'bpm': bpm,
            'musical_key': musical_key,
            'duration_seconds': duration,
            'loudness_lufs': loudness,
            'sample_rate': sr,
            'channels': channels,
            'bit_depth': None,  # Difficult to determine from loaded array
        }
    except Exception as e:
        raise Exception(f"Audio analysis failed: Unable to process the file. Please try again or contact support if the issue persists.")


def mix_audio(input_path: Path, output_path: Path, genre: Optional[str] = None) -> None:
    """Apply automated mixing to audio file."""
    try:
        # Load audio
        y, sr = librosa.load(str(input_path), sr=None, mono=False)
        
        # Handle stereo/mono
        if y.ndim == 1:
            y = np.stack([y, y])  # Convert mono to stereo
        
        # Normalize levels
        max_val = np.abs(y).max()
        if max_val > 0:
            y = y / max_val * 0.8  # Normalize to -1.9 dB
        
        # Apply light compression (simplified)
        threshold = 0.5
        ratio = 3.0
        y_compressed = np.where(
            np.abs(y) > threshold,
            threshold + (np.abs(y) - threshold) / ratio,
            y
        ) * np.sign(y)
        
        # Balance stereo image (ensure not too wide)
        if y_compressed.shape[0] == 2:
            mid = (y_compressed[0] + y_compressed[1]) / 2
            side = (y_compressed[0] - y_compressed[1]) / 2
            # Reduce side width slightly
            side = side * 0.9
            y_compressed[0] = mid + side
            y_compressed[1] = mid - side
        
        # Save as WAV
        import soundfile as sf
        sf.write(str(output_path), y_compressed.T, sr, subtype='PCM_24')
        
    except Exception as e:
        raise Exception(f"Mixing failed: Unable to process the file. Please ensure it's a valid audio format.")


def master_audio(input_path: Path, output_wav: Path, output_mp3: Optional[Path] = None, 
                 genre: Optional[str] = None, target_lufs: float = -14.0) -> None:
    """Apply mastering to audio file with LUFS targeting."""
    try:
        # Load audio
        y, sr = librosa.load(str(input_path), sr=None, mono=False)
        
        # Handle stereo/mono
        if y.ndim == 1:
            y = np.stack([y, y])
        
        # Measure current loudness
        meter = pyln.Meter(sr)
        current_loudness = meter.integrated_loudness(y.T)
        
        # Normalize to target LUFS
        y_normalized = pyln.normalize.loudness(y.T, current_loudness, target_lufs).T
        
        # Apply gentle limiting
        y_limited = np.clip(y_normalized, -0.99, 0.99)
        
        # Final polish EQ (very subtle high-shelf boost)
        # This is a simplified version; in production would use proper filtering
        
        # Save WAV
        import soundfile as sf
        sf.write(str(output_wav), y_limited.T, sr, subtype='PCM_24')
        
        # Save MP3 if requested
        if output_mp3:
            audio_segment = AudioSegment.from_wav(str(output_wav))
            audio_segment.export(str(output_mp3), format='mp3', bitrate='320k')
            
    except Exception as e:
        raise Exception(f"Mastering failed: Unable to process the file. Check that all audio content is valid.")
