# Zeusonic 1.0 🚀

**Production-ready AI-powered music transformation platform.**

Status: ✅ **READY FOR LAUNCH**

---

## Features

### Core Capabilities
- **Beat Transformation:** Transform any audio to Amapiano, Afrobeats, Reggae, House, or Hip-Hop
- **Audio Analysis:** Automatic BPM and musical key detection (librosa)
- **Stem Separation:** Isolate vocals, drums, bass, and other instruments (HPSS)
- **Professional Mixing:** Combine transforms with original audio
- **Mastering:** Professional loudness normalization (LUFS target: -14)
- **Download with Stems:** Export transformed tracks + separated stems

### User Features
- **User Authentication:** Email + password, JWT tokens (60min expiry)
- **Project Management:** Create, organize, and archive projects
- **Subscription Billing:** Free (2 projects) and Pro (unlimited) plans via Stripe
- **Audit Trail:** Full compliance logging of user actions
- **Observability:** Structured job logging for troubleshooting

---

## Getting Started

### Quick Start (Development)

1. **Setup environment:**
   ```bash
   cd /Users/administrator/zeusonic
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

2. **Install system dependencies:**
   ```bash
   # Verify FFmpeg is installed
   which ffmpeg  # Should output: /usr/local/bin/ffmpeg
   
   # If not installed:
   brew install ffmpeg
   ```

3. **Initialize database:**
   ```bash
   cd backend
   alembic upgrade head
   ```

4. **Start backend:**
   ```bash
   cd backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Start frontend (in separate terminal):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

6. **Access:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API docs: http://localhost:8000/docs

### Golden Path Test (End-to-End Verification)

Run the comprehensive 15-step verification:

```bash
cd backend
python -m pytest tests/test_golden_path.py -v
```

This verifies:
1. User registration
2. Email verification
3. Login
4. Project creation
5. Audio upload
6. Track analysis (BPM + key detection)
7. Beat transformation (Amapiano)
8. Beat transformation (Afrobeats)
9. Audio mixing
10. Audio mastering
11. Stem export
12. Master track download
13. Stripe subscription checkout
14. Webhook subscription creation
15. Project limit enforcement (Pro plan)

---

## API Reference

### Authentication
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/verify-email
```

### Projects
```
GET  /api/v1/projects
POST /api/v1/projects
GET  /api/v1/projects/{project_id}
```

### Audio Processing
```
POST /api/v1/projects/{project_id}/audio/upload
GET  /api/v1/audio/{track_id}
POST /api/v1/audio/{track_id}/analyze
GET  /api/v1/audio/{track_id}/analyze/status
POST /api/v1/audio/{track_id}/transform
GET  /api/v1/audio/{track_id}/transform/status
```

### Billing
```
GET  /api/v1/billing/status
POST /api/v1/billing/checkout
POST /api/v1/billing/webhooks/stripe
GET  /api/v1/billing/subscribe-free
```

Full API docs: `GET /docs` (Swagger UI)

---

## Architecture

### Backend Stack
- **Framework:** FastAPI 0.68.0+
- **Database:** SQLAlchemy + Alembic (SQLite for dev, PostgreSQL ready)
- **Audio Processing:** librosa, scipy (HPSS), soundfile, pydub, pyloudnorm
- **Authentication:** PyJWT, passlib[bcrypt]
- **Payments:** Stripe API
- **Observability:** Structured JSON logging, AuditLog database model

### Frontend Stack
- **Framework:** Next.js 13+
- **Styling:** TailwindCSS
- **State:** React Context
- **Deployment:** Vercel-ready

### File Structure
```
zeusonic/
├── backend/
│   ├── main.py                    # FastAPI app
│   ├── requirements.txt            # Python dependencies
│   ├── api/
│   │   └── v1/                    # API endpoints
│   │       ├── health.py          # Health checks
│   │       ├── auth.py            # Authentication
│   │       ├── projects.py        # Project management
│   │       ├── audio_tracks.py    # Audio upload/analysis/processing
│   │       ├── audio_transform.py # Beat transformation
│   │       ├── billing.py         # Stripe integration
│   │       └── meta.py            # Metadata endpoints
│   ├── core/
│   │   ├── config.py              # Configuration
│   │   ├── logging.py             # Logging setup
│   │   ├── observability.py       # Job/audit logging
│   │   └── auth.py                # JWT utilities
│   ├── db/
│   │   ├── database.py            # SQLAlchemy session
│   │   ├── models.py              # Data models
│   │   └── migrations/            # Alembic migrations
│   ├── services/
│   │   └── audio_processor.py     # Audio algorithms
│   ├── storage/                   # Project files (by project_id)
│   └── alembic/                   # Database migrations (0001-0007)
├── frontend/
│   ├── pages/
│   │   ├── auth.tsx               # Login/register
│   │   ├── studio.tsx             # Transform interface
│   │   ├── dashboard.tsx          # Project listing
│   │   └── billing.tsx            # Subscription management
│   ├── components/                # Reusable React components
│   ├── styles/                    # TailwindCSS
│   └── next.config.js
└── docs/
    └── API.md                     # API documentation
```

---

## Observability & Monitoring

### Structured Logging
All jobs emit JSON logs:
```json
{
  "timestamp": "2026-02-02T15:30:45.123456",
  "event_type": "job",
  "job_type": "audio_analysis",
  "job_id": 1,
  "user_id": 5,
  "project_id": 2,
  "status": "completed",
  "duration_ms": 17333,
  "metadata": {"bpm": 120.5, "key": "A"}
}
```

### Audit Trail
All user actions logged to `audit_logs` table:
- Project creation
- Audio uploads
- Transform completions
- Subscription changes

Query example:
```sql
SELECT * FROM audit_logs 
WHERE user_id = ? 
ORDER BY created_at DESC 
LIMIT 50;
```

### Job Status
Monitor jobs via status endpoints:
```
GET /api/v1/audio/{track_id}/analyze/status
GET /api/v1/audio/{track_id}/transform/status
```

---

## Deployment

### Pre-Deployment Checklist

1. **Database Migration:**
   ```bash
   alembic upgrade head
   ```
   This applies all 7 migrations (0001-0007_add_audit_logs)

2. **Environment Configuration:**
   ```bash
   # backend/.env
   JWT_SECRET=<generate-secure-32-char-string>
   STRIPE_API_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   DATABASE_URL=postgresql://...  # Optional, defaults to SQLite
   ```

3. **System Dependencies:**
   ```bash
   ffmpeg --version  # Must be installed and in PATH
   ```

4. **File Storage:**
   - Ensure `backend/storage/` directory writable
   - Configure cloud storage (S3) in production
   - Backup storage daily

5. **Monitoring Setup:**
   - Forward logs to ELK/DataDog/Splunk
   - Set alerts for failed jobs (status='failed')
   - Monitor HTTP error rates

### Production Deployment Options

**Option 1: Heroku**
```bash
heroku create zeusonic
git push heroku main
heroku config:set JWT_SECRET=... STRIPE_API_KEY=...
```

**Option 2: AWS**
- Backend: API Gateway + Lambda (FastAPI via Zappa)
- Frontend: CloudFront + S3
- Database: RDS PostgreSQL
- Storage: S3 (configured in config.py)

**Option 3: DigitalOcean**
- App Platform (managed FastAPI)
- Managed PostgreSQL database
- Spaces object storage

---

## Testing

### Unit Tests
```bash
pytest tests/ -v
```

### Golden Path (E2E)
```bash
pytest tests/test_golden_path.py -v
```

### Smoke Tests (Health Check)
```bash
pytest tests/test_smoke.py -v
```

---

## Troubleshooting

### Audio Processing Failures
1. Check FFmpeg: `which ffmpeg`
2. Check file format: MP3, WAV, or FLAC
3. Check file size: Max 100MB
4. Check logs: `grep -i error backend/logs/*.log`

### Stripe Webhook Failures
1. Verify webhook secret configured
2. Check Stripe dashboard event log
3. Retry webhook: Stripe Dashboard → Endpoints → Retry

### High Latency
1. Check CPU usage (should be <80%)
2. Check disk I/O (audio processing is CPU-bound)
3. Consider scaling up instance

### Database Issues
1. Verify Alembic migrations: `alembic current`
2. Check connectivity: `psql $DATABASE_URL`
3. Backup database before upgrades

---

## Support & Contributing

- **Documentation:** See [ZEUSONIC_1.0_OBSERVABILITY_HARDENING.md](ZEUSONIC_1.0_OBSERVABILITY_HARDENING.md)
- **Launch Guide:** See [LAUNCH_READINESS_CHECKLIST.md](LAUNCH_READINESS_CHECKLIST.md)
- **Issues:** Report via GitHub issues
- **Security:** Report to security@zeusonic.dev

---

## License

Zeusonic 1.0 © 2026 ZeusTech. All rights reserved.
