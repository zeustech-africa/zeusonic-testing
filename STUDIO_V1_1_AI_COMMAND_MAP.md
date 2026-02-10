# Zeusonic Studio V1.1 — AI Command Map

Date: 10 February 2026

## Control → AI Command Mapping

### Upload Track (JWT Project Upload)
- Control: Upload track
- Endpoint: POST /api/v1/projects/{project_id}/audio
- Payload: multipart/form-data with file
- Result: Track created with track_id (used for AI commands)

### Upload → Analyze
- Control: Upload audio
- Endpoint: POST /api/v1/ai/analyze
- Payload:
  - project_id
  - track_id
- Result: Analysis job queued, track status moves to analyzing/analyzed.

### Style Transform Panel
- Control: Genre + Mood + Tempo Bias + Energy + Transform button
- Endpoint: POST /api/v1/ai/transform
- Payload:
  - project_id
  - track_id
  - style
  - mood
  - tempo_bias
  - energy
- Result: Beat transform job queued, status reflected inline.

### Mixer Panel
- Control: Bass / Treble / Presence / Stereo width sliders
- Endpoint: POST /api/v1/ai/mix-adjust
- Payload:
  - project_id
  - track_id
  - bass
  - treble
  - presence
  - width
- Result: AI mix adjustment job queued, status reflected inline.

### Instrument Add Panel
- Control: Bass / Piano / Synth / Guitar / Drums buttons
- Endpoint: POST /api/v1/ai/instrument-add
- Payload:
  - project_id
  - track_id
  - instrument_type
  - intensity
  - placement
- Result: AI instrument layer queued (background render).

### Export
- Control: Export button
- Endpoint: POST /api/v1/ai/export
- Payload:
  - project_id
  - track_id
- Result: If a master/mix exists, download URL returned; otherwise a master export job is queued.

## Safety & Scope Notes
- All AI commands require JWT authentication.
- Commands are scoped to project_id + track_id.
- No auth or schema changes introduced.
- UI uses inline status (no alerts).

## Supporting Endpoints (Waveform)
- GET /api/v1/audio/{track_id}/source/download (original waveform source)
- GET /api/v1/audio/{track_id}/transform/download (transform waveform source)
- GET /api/v1/audio/download/{track_id}/mix (mix waveform source)
- GET /api/v1/audio/download/{track_id}/master (master waveform source)
