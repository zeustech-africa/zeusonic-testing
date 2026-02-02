# Zeusonic 1.0 — Quick Launch Guide

**Status:** ✅ Ready for Production  
**Last Updated:** 2026-02-02

---

## 30-Second Launch Summary

Zeusonic 1.0 is production-ready with music transformation, Stripe billing, and comprehensive observability. All 5 phases complete, all tests passing.

---

## Pre-Launch (Run Once)

### 1. Apply Database Migration

```bash
cd /Users/administrator/zeusonic/backend
alembic upgrade head
```

This applies migration 0007_add_audit_logs and creates the audit_logs table.

### 2. Configure Environment

Create/update `backend/.env`:

```bash
JWT_SECRET=your-secure-32-character-random-string
STRIPE_API_KEY=sk_live_... (or sk_test_... for testing)
STRIPE_WEBHOOK_SECRET=whsec_... (from Stripe dashboard)
```

### 3. Verify FFmpeg

```bash
which ffmpeg
# Should output: /usr/local/bin/ffmpeg
# If not installed: brew install ffmpeg
```

### 4. Install Dependencies

```bash
cd /Users/administrator/zeusonic/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Launch (Development)

### Terminal 1: Start Backend

```bash
cd /Users/administrator/zeusonic/backend
source .venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: **http://localhost:8000**  
API docs: **http://localhost:8000/docs**

### Terminal 2: Start Frontend

```bash
cd /Users/administrator/zeusonic/frontend
npm install
npm run dev
```

Frontend will be available at: **http://localhost:3000**

---

## Verify Launch

### Option A: Golden Path Test (Automated)

```bash
cd /Users/administrator/zeusonic/backend
pytest tests/test_golden_path.py -v
```

This runs all 15 steps end-to-end and verifies everything works.

### Option B: Manual Test Flow

1. **Register:** http://localhost:3000/auth → Create account
2. **Create Project:** Dashboard → New Project
3. **Upload Audio:** Studio → Upload MP3/WAV
4. **Transform:** Choose Amapiano → Wait for completion
5. **Download:** Download master or stems
6. **Billing:** Dashboard → Billing → Checkout → Stripe test card (4242...)
7. **Verify Pro Plan:** After checkout, can create unlimited projects

---

## Production Deployment

### Heroku Quick Deploy

```bash
cd /Users/administrator/zeusonic

# Create app
heroku create zeusonic-prod

# Configure environment
heroku config:set JWT_SECRET=your-secure-string
heroku config:set STRIPE_API_KEY=sk_live_...
heroku config:set STRIPE_WEBHOOK_SECRET=whsec_...

# Deploy
git push heroku main

# Run migration
heroku run "cd backend && alembic upgrade head"

# Check logs
heroku logs --tail
```

### AWS Lambda + API Gateway

```bash
cd /Users/administrator/zeusonic/backend

# Install Zappa
pip install zappa

# Initialize Zappa
zappa init

# Deploy
zappa deploy dev  # Or prod

# Update webhook
# Stripe Dashboard → Webhook Endpoints → Add: https://your-api.amazonaws.com/api/v1/billing/webhooks/stripe
```

### DigitalOcean App Platform

1. Push repo to GitHub
2. Connect DigitalOcean App Platform to GitHub
3. Create PostgreSQL database
4. Set environment variables (JWT_SECRET, STRIPE keys)
5. Deploy
6. Run migration: `doctl apps exec zeusonic backend -- alembic upgrade head`

---

## Post-Launch Verification Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads at http://localhost:3000
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Can register user
- [ ] Can login
- [ ] Can create project
- [ ] Can upload audio file
- [ ] Can analyze audio (BPM + key detected)
- [ ] Can transform to Amapiano
- [ ] Can download master
- [ ] Can download stems
- [ ] Stripe checkout loads
- [ ] Can subscribe (test card: 4242 4242 4242 4242)
- [ ] Audit logs being recorded (check database)
- [ ] Job logs being emitted (check stdout)

---

## Troubleshooting

### Backend won't start

```bash
# Check Python version (3.8+ required)
python --version

# Check dependencies
pip install -r requirements.txt --upgrade

# Check FFmpeg
which ffmpeg || brew install ffmpeg

# Check database
alembic current  # Should show: 0007_add_audit_logs
```

### Frontend won't start

```bash
cd frontend
rm -rf node_modules .next package-lock.json
npm install
npm run dev
```

### Audio processing fails

```bash
# Check FFmpeg works
ffmpeg -version

# Check file format (MP3, WAV, FLAC only)
file /path/to/audio.mp3

# Check file size (<100MB)
du -h /path/to/audio.mp3
```

### Stripe webhook not working

1. Check `.env` has `STRIPE_WEBHOOK_SECRET`
2. Check Stripe dashboard webhook endpoint configured
3. Check backend is publicly accessible (required for webhooks)
4. Re-trigger webhook from Stripe dashboard

### Database migration fails

```bash
# Check current migration
alembic current

# Show history
alembic history

# Downgrade if needed
alembic downgrade -1

# Re-upgrade
alembic upgrade head
```

---

## Monitoring & Logs

### View Job Logs

```bash
# Terminal running backend (see stdout)
# Look for JSON lines like:
# {"timestamp": "...", "event_type": "job", "job_type": "audio_analysis", ...}
```

### Query Audit Trail

```bash
# In a Python REPL
from backend.db.database import SessionLocal
from backend.db.models import AuditLog

session = SessionLocal()
logs = session.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(50)
for log in logs:
    print(f"{log.created_at} | {log.event_type} | {log.action} | {log.details}")
```

### Monitor Job Status

```bash
# Check all failed jobs
from backend.db.database import SessionLocal
from backend.db.models import AudioProcessing, BeatTransformJob

session = SessionLocal()
failed_jobs = session.query(BeatTransformJob).filter_by(status='failed').all()
for job in failed_jobs:
    print(f"Transform {job.id}: {job.status}")
```

---

## Key URLs & Credentials

| Service | URL | Default Auth |
|---------|-----|--------------|
| Frontend | http://localhost:3000 | Register via UI |
| Backend API | http://localhost:8000 | JWT token from /api/v1/auth/login |
| API Docs | http://localhost:8000/docs | No auth needed |
| Stripe Test | Use card 4242 4242 4242 4242 | Expiry: Any future date, CVV: Any 3 digits |
| Database | sqlite:///backend/zeusonic.db | No auth (SQLite) |

---

## Important Notes

1. **Migration Required:** Always run `alembic upgrade head` before launch
2. **JWT Secret:** Must be 32+ characters and secure
3. **Stripe Keys:** Test keys for development, live keys for production
4. **FFmpeg:** Required for audio mastering
5. **Database:** SQLite for dev (portable), PostgreSQL recommended for production
6. **File Storage:** Defaults to `backend/storage/`, configure S3 for production
7. **Email:** Optional (verification not enforced), use SendGrid for production

---

## Success Metrics (First Week)

- Uptime: >99.5%
- Error rate: <1% of requests
- Job success: >95% (audio quality dependent)
- Webhook success: 100% (all Stripe events processed)
- Audit logs: 100% (all user actions recorded)
- Response time: <500ms (p95)

---

## Support Resources

- **Full Docs:** See IMPLEMENTATION_SUMMARY.md
- **Observability:** See ZEUSONIC_1.0_OBSERVABILITY_HARDENING.md
- **Deployment Checklist:** See LAUNCH_READINESS_CHECKLIST.md
- **API Reference:** GET /docs (Swagger UI)

---

## Next Steps (Post-Launch)

1. **Day 1:** Monitor error rates, Stripe webhooks, job success rate
2. **Week 1:** Gather user feedback, identify most-used features
3. **Week 2:** Plan Phase 6 (custom templates, advanced features)
4. **Month 1:** Analyze usage patterns, optimize performance

---

## Emergency Contacts

- **Critical Issues:** Restart backend + check logs
- **Stripe Issues:** Stripe Dashboard → Logs or support@stripe.com
- **Database Issues:** Backup + run `alembic upgrade head` + restart
- **Security Issues:** security@zeusonic.dev

---

## 🚀 You're Ready to Launch!

Zeusonic 1.0 is production-ready. Run the quick launch commands above and you'll be live in minutes.

**Questions?** See IMPLEMENTATION_SUMMARY.md for comprehensive documentation.
