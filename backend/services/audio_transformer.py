from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import librosa
import soundfile as sf

from core.logging import get_logger

logger = get_logger(__name__)

STYLE_TEMPLATES: Dict[str, List[Tuple[int, float]]] = {
    # 16-step patterns (1 bar of 4/4 at 16th-note resolution)
    "amapiano": [(0, 1.0), (3, 0.6), (7, 0.8), (8, 1.0), (12, 0.7), (14, 0.6)],
    "afrobeats": [(0, 1.0), (4, 0.6), (6, 0.7), (8, 1.0), (11, 0.6), (12, 0.8)],
    "reggae": [(4, 0.8), (8, 0.7), (12, 0.8)],
    "house": [(0, 1.0), (4, 0.9), (8, 1.0), (12, 0.9)],
    "hiphop": [(0, 1.0), (6, 0.6), (8, 0.8), (12, 0.7)],
}

SUPPORTED_STYLES = set(STYLE_TEMPLATES.keys())


@dataclass
class RhythmAnalysis:
    bpm: float
    time_signature: str
    groove_pattern: List[float]
    swing_ratio: float


def analyze_rhythm(track_path: Path) -> RhythmAnalysis:
    """Analyze rhythm characteristics of a track."""
    y, sr = librosa.load(track_path, sr=None, mono=True)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

    # Estimate groove pattern via onset strength across 16 steps
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    if len(beat_frames) < 2:
        groove = [0.0] * 16
    else:
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        duration = beat_times[-1] - beat_times[0]
        if duration <= 0:
            groove = [0.0] * 16
        else:
            step_times = np.linspace(beat_times[0], beat_times[-1], num=16, endpoint=False)
            step_frames = librosa.time_to_frames(step_times, sr=sr)
            groove = [float(onset_env[min(i, len(onset_env) - 1)]) for i in step_frames]
            max_val = max(groove) if groove else 0.0
            if max_val > 0:
                groove = [g / max_val for g in groove]

    # Swing ratio estimation (simple heuristic on inter-beat intervals)
    swing_ratio = 0.5
    if len(beat_frames) >= 4:
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        intervals = np.diff(beat_times)
        if len(intervals) >= 2:
            even = np.mean(intervals[::2]) if len(intervals[::2]) else 0.0
            odd = np.mean(intervals[1::2]) if len(intervals[1::2]) else 0.0
            if even + odd > 0:
                swing_ratio = float(odd / (even + odd))

    return RhythmAnalysis(
        bpm=float(tempo),
        time_signature="4/4",
        groove_pattern=groove,
        swing_ratio=swing_ratio,
    )


def extract_stems(track_path: Path, stems_dir: Path) -> Dict[str, Path]:
    """Extract stems using HPSS (drums vs harmonic)."""
    y, sr = librosa.load(track_path, sr=None, mono=False)
    if y.ndim == 1:
        y = np.expand_dims(y, axis=0)

    y_harmonic, y_percussive = librosa.effects.hpss(y)

    stems_dir.mkdir(parents=True, exist_ok=True)
    drums_path = stems_dir / "drums.wav"
    harmonic_path = stems_dir / "harmonic.wav"

    sf.write(drums_path, y_percussive.T, sr, subtype="PCM_24")
    sf.write(harmonic_path, y_harmonic.T, sr, subtype="PCM_24")

    return {"drums": drums_path, "harmony": harmonic_path}


def _render_style_pattern(sr: int, tempo: float, duration: float, style: str, swing_ratio: float) -> np.ndarray:
    """Generate a percussive groove based on a style template."""
    pattern = STYLE_TEMPLATES.get(style)
    if not pattern:
        raise ValueError(f"Unsupported style: {style}")

    seconds_per_beat = 60.0 / max(tempo, 1e-6)
    steps_per_beat = 4  # 16th-note resolution
    seconds_per_step = seconds_per_beat / steps_per_beat

    # Apply swing to off-steps (8th-note swing)
    swing_offset = (swing_ratio - 0.5) * seconds_per_step

    click_times = []
    bar_duration = seconds_per_beat * 4
    bar_count = int(np.ceil(duration / bar_duration))

    for bar in range(bar_count):
        bar_start = bar * bar_duration
        for step, strength in pattern:
            time = bar_start + (step * seconds_per_step)
            # Apply swing to odd steps (off-beats)
            if step % 2 == 1:
                time += swing_offset
            if time < duration:
                click_times.append((time, strength))

    times = [t for t, _ in click_times]
    strengths = [s for _, s in click_times]

    clicks = librosa.clicks(
        times=times,
        sr=sr,
        length=int(duration * sr),
        click_freq=1500.0,
        click_duration=0.01,
    )

    # Apply strength envelope
    if strengths:
        envelope = np.zeros_like(clicks)
        for t, s in click_times:
            idx = int(t * sr)
            if idx < len(envelope):
                envelope[idx] += s
        envelope = np.clip(envelope, 0.0, 1.0)
        clicks = clicks * (0.6 + 0.4 * envelope)

    return clicks


def reassemble_track(harmonic: np.ndarray, percussive: np.ndarray) -> np.ndarray:
    """Blend harmonic and percussive layers, then normalize."""
    mix = harmonic + percussive
    peak = np.max(np.abs(mix)) if mix.size else 1.0
    if peak > 0:
        mix = mix / peak * 0.98
    return mix


def transform_beat(track_path: Path, target_style: str, output_path: Path) -> Dict[str, float]:
    """Transform the rhythmic layer while preserving harmony and structure."""
    analysis = analyze_rhythm(track_path)
    y, sr = librosa.load(track_path, sr=None, mono=False)
    if y.ndim == 1:
        y = np.expand_dims(y, axis=0)

    y_harmonic, y_percussive = librosa.effects.hpss(y)

    duration = y.shape[1] / sr
    style = target_style.lower()

    # Generate new percussive layer
    clicks = _render_style_pattern(sr, analysis.bpm, duration, style, analysis.swing_ratio)
    clicks = np.expand_dims(clicks, axis=0)

    # Match percussive energy
    perc_rms = np.sqrt(np.mean(y_percussive ** 2)) if y_percussive.size else 0.0
    click_rms = np.sqrt(np.mean(clicks ** 2)) if clicks.size else 1.0
    gain = (perc_rms / click_rms) if click_rms > 0 else 1.0
    clicks = clicks * gain

    # Reassemble with harmonic layer
    mix = reassemble_track(y_harmonic, clicks)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, mix.T, sr, subtype="PCM_24")

    return {
        "bpm": analysis.bpm,
        "swing_ratio": analysis.swing_ratio,
    }
