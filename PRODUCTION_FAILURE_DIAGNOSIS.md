# ZEUSONIC PRODUCTION FAILURE DIAGNOSIS & REMEDIATION
**Engineer:** GitHub Copilot (DevOps + Backend Release)  
**Date:** 8 February 2026  
**Issue:** /auth/register returns HTTP 500 on live Render despite fix being pushed  
**Severity:** CRITICAL - Production blocking

---

## SECTION 1: CODE VERSION VERIFICATION ✅

### GitHub Repository State
```
Current HEAD: 9a7184c744bc90485e0c4c3cbf4c7ea0f2da044e
Commit: fix: wire Alembic migrations into production startup and add project root alembic.ini
Status: ✅ VERIFIED
```

### Dockerfile CMD (CONFIRMED CORRECT)
```dockerfile
CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```
✅ Alembic runs BEFORE uvicorn startup

### Migration 0008 (CONFIRMED PRESENT)
```
File: backend/alembic/versions/0008_add_otp_fields.py
Head: 0008_add_otp_fields
Adds: otp_hash, otp_expires_at columns
Status: ✅ IDEMPOTENT (checks if columns exist)
```

### Render Configuration (CONFIRMED AUTO-DEPLOY)
```yaml
name: zeusonic-backend
autoDeploy: true
```
✅ Auto-deploy is enabled - should trigger on push to main

---

## SECTION 2: SUSPECTED ROOT CAUSE

**DIAGNOSIS:** Render is likely running a **cached or stale container** that does not include commit `9a7184c`.

**Evidence:**
1. ✅ Local code is correct (commit 9a7184c)
2. ✅ Git push succeeded (confirmed in release report)
3. ❌ Render still returning HTTP 500 on /auth/register
4. **Hypothesis:** Render either:
   - Did not detect the git push webhook
   - Built container but didn't restart service
   - Cached Docker layers from before the fix
   - Failed during `alembic upgrade head` silently

---

## SECTION 3: LIVE CONTAINER AUDIT (REQUIRED STEPS)

### Access Render Container Shell

**Step 1: Go to Render Dashboard**
1. Navigate to https://dashboard.render.com
2. Select service: `zeusonic-backend`
3. Click "Shell" tab (or "Console")

**Step 2: Verify Git Commit (if available)**
```bash
# Check if git is available in container
git rev-parse HEAD 2>/dev/null || echo "Git not in container"

# Alternative: Check if commit hash is in environment
echo $RENDER_GIT_COMMIT
```

**Step 3: Verify Alembic State**
```bash
cd /app
alembic current
alembic heads
```

**Expected output:**
```
0008_add_otp_fields (head)
0008_add_otp_fields (head)
```

**Step 4: Inspect SQLite Schema (CRITICAL)**
```bash
cd /app
sqlite3 backend/storage/zeusonic.db "PRAGMA table_info(users);" | grep -E "otp_hash|otp_expires_at"
```

**Expected output:**
```
6|otp_hash|VARCHAR(255)|0||0
7|otp_expires_at|DATETIME|0||0
```

**If columns are MISSING:**
```bash
# Check if alembic_version table exists
sqlite3 backend/storage/zeusonic.db "SELECT * FROM alembic_version;"
```

**Step 5: Check Container Logs**
```bash
# Look for migration output in logs
grep -i "alembic\|migration" /var/log/* 2>/dev/null
```

---

## SECTION 4: FAILURE ANALYSIS MATRIX

### Scenario A: Columns EXIST but endpoint still fails
**Root Cause:** Code logic error (unlikely, tested locally)

**Diagnosis:**
```bash
# Trigger registration and capture full error
curl -X POST https://zeusonic-backend.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}' \
  -v
```

**Look for:**
- Full stack trace in Render logs
- SQLAlchemy error messages
- JWT_SECRET missing error
- Resend API key error

### Scenario B: Columns MISSING
**Root Cause:** Alembic did not run OR failed silently

**Sub-scenarios:**
1. **Alembic never executed:** Docker CMD didn't run
2. **Alembic failed:** Migration error but container started anyway
3. **Old container still running:** Deploy didn't trigger restart

**Diagnosis from alembic_version table:**
```bash
sqlite3 backend/storage/zeusonic.db "SELECT version_num FROM alembic_version;"
```

**If shows < 0008:** Alembic ran but didn't reach 0008
**If table doesn't exist:** Alembic never ran
**If shows 0008:** Columns should exist (check PRAGMA output again)

### Scenario C: Render Didn't Deploy New Code
**Root Cause:** Webhook failed or deploy disabled

**Diagnosis:**
1. Check Render dashboard "Events" tab for deploy history
2. Look for commit hash `9a7184c` in deploy list
3. Check deploy status (success/failed/cancelled)

---

## SECTION 5: DEFINITIVE REMEDIATION PLAN

### PLAN A: Force Clean Rebuild (RECOMMENDED IF SCENARIO C)

**Steps:**
1. Go to Render dashboard → zeusonic-backend
2. Click "Manual Deploy" dropdown
3. Select "Clear build cache & deploy"
4. Wait for build to complete (~5-10 minutes)
5. Verify in logs: Look for "alembic upgrade head" output
6. Test registration endpoint

**Why this works:**
- Forces Docker to rebuild all layers
- Guarantees new code is pulled from GitHub
- Runs migrations fresh on startup

### PLAN B: Manual Migration Execution (IF SCENARIO B)

**Steps:**
1. Go to Render Shell
2. Execute:
```bash
cd /app
alembic upgrade head
```
3. Verify output shows migration applied
4. Restart service (no rebuild needed)
5. Test registration endpoint

**Why this works:**
- Directly applies missing migration
- Doesn't require rebuild
- Faster than Plan A

**Risk:** If container code is still old, will fail again on restart

### PLAN C: Force Restart Without Rebuild (IF CODE IS CURRENT)

**Steps:**
1. Go to Render dashboard → zeusonic-backend
2. Click "Manual Deploy" → "Deploy latest commit"
3. OR: Click "Restart" if deploy is current
4. Wait for restart (~1-2 minutes)
5. Test registration endpoint

**Why this works:**
- If code is current but process crashed, restart fixes
- Migrations run on startup via Dockerfile CMD
- Fastest option

**Risk:** Won't help if old code is cached

---

## SECTION 6: RECOMMENDED EXECUTION SEQUENCE

**DO THIS IN ORDER:**

### Phase 1: Diagnosis (5 minutes)
1. Access Render Dashboard
2. Check "Events" tab for latest deploy
3. Verify commit hash is `9a7184c`
4. If NO → Proceed to Phase 2 Plan A
5. If YES → Proceed to Phase 2 Plan C, then Plan B if fails

### Phase 2: Remediation (10-15 minutes)
**If commit is NOT 9a7184c:**
- Execute **PLAN A: Force Clean Rebuild**
- This guarantees fresh code and migrations

**If commit IS 9a7184c:**
- Execute **PLAN C: Force Restart**
- If still fails → Access Shell and run **PLAN B: Manual Migration**

### Phase 3: Verification (5 minutes)
1. Wait for deploy/restart to complete
2. Check Render logs for:
   ```
   INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
   INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
   Running upgrade 0007_add_audit_logs -> 0008_add_otp_fields
   ```
3. Test registration:
   ```bash
   curl -X POST https://zeusonic-backend.onrender.com/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"devops-test-$(date +%s)@example.com","password":"TestPass123!"}'
   ```
4. Expected response:
   ```json
   {
     "email": "devops-test-1234567890@example.com",
     "is_verified": false,
     "message": "Verification code sent to devops-test-1234567890@example.com. Check your inbox."
   }
   ```
5. Status code: **HTTP 201**

---

## SECTION 7: VERIFICATION CHECKLIST

After remediation, verify ALL of the following:

### ✅ Container State
- [ ] Render dashboard shows commit `9a7184c`
- [ ] Container logs show "alembic upgrade head" execution
- [ ] No migration errors in logs

### ✅ Database State
```bash
# Run in Render Shell
sqlite3 backend/storage/zeusonic.db "SELECT version_num FROM alembic_version;"
# Expected: 0008_add_otp_fields

sqlite3 backend/storage/zeusonic.db "PRAGMA table_info(users);" | grep -E "otp_hash|otp_expires_at"
# Expected: Both columns present
```

### ✅ Endpoint Behavior
```bash
# Test registration
curl -X POST https://zeusonic-backend.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"verify-$(date +%s)@example.com","password":"SecurePass123!"}'
```

**Expected responses:**
- **HTTP 201:** ✅ SUCCESS
- **HTTP 409:** Email already exists (also success - means DB working)
- **HTTP 400:** Validation error (check password requirements)
- **HTTP 500:** ❌ FAILURE - review logs

### ✅ OTP Email Delivery (IF RESEND CONFIGURED)
- Check email inbox for OTP code
- If no email: Check Resend API key in Render env vars
- Email failure is logged but doesn't block registration (HTTP 201 still returned)

---

## SECTION 8: FINAL REPORT TEMPLATE

**After completing remediation, fill this in:**

### Deployment Status
```
Render Commit Hash: [CHECK IN DASHBOARD]
Expected Hash: 9a7184c744bc90485e0c4c3cbf4c7ea0f2da044e
Match: [YES/NO]
```

### Container State
```
Alembic Current: [OUTPUT OF alembic current]
Alembic Heads: [OUTPUT OF alembic heads]
Match: [YES/NO]
```

### Database Schema
```
otp_hash column: [PRESENT/MISSING]
otp_expires_at column: [PRESENT/MISSING]
```

### Endpoint Test
```
POST /auth/register status: [HTTP CODE]
Response: [JSON RESPONSE OR ERROR]
Success: [YES/NO]
```

### Verdict
```
✅ Render is running the fixed version: [YES/NO]
✅ Issue is resolved: [YES/NO]
✅ Registration works: [YES/NO]
```

### Root Cause (After Investigation)
```
[DESCRIBE WHAT WAS WRONG - e.g., "Render cached old Docker layers", "Migration didn't run", etc.]
```

### Resolution Applied
```
[DESCRIBE WHAT YOU DID - e.g., "Forced clean rebuild via Render dashboard", "Manually ran alembic upgrade head"]
```

---

## SECTION 9: EMERGENCY FALLBACK

**If ALL remediation plans fail:**

### Nuclear Option: Reset Persistent Disk (LAST RESORT)

**⚠️ WARNING: THIS DELETES ALL USER DATA**

**Only do this if:**
1. Persistent disk is corrupted beyond repair
2. Migration is permanently stuck
3. No production users exist yet (pre-launch)

**Steps:**
1. Backup database first:
   ```bash
   # In Render Shell
   cp backend/storage/zeusonic.db backend/storage/zeusonic.db.backup-$(date +%s)
   ```
2. Go to Render dashboard → zeusonic-backend → "Disks"
3. Delete disk `zeusonic-storage`
4. Redeploy service (will create fresh disk)
5. Migrations will run on fresh database

**Result:** Clean slate, all user data lost

**Alternative (if users exist):** Export users table, recreate, import:
```bash
sqlite3 backend/storage/zeusonic.db ".dump users" > users_backup.sql
# Delete and recreate disk
# After redeploy:
sqlite3 backend/storage/zeusonic.db < users_backup.sql
```

---

## SECTION 10: PREVENTIVE MEASURES

**To prevent this issue in future:**

### 1. Add Health Check Endpoint
```python
# backend/api/v1/health.py
@router.get("/health/migrations")
def check_migrations(db: Session = Depends(get_db)):
    """Verify migration state"""
    result = db.execute(text("SELECT version_num FROM alembic_version")).fetchone()
    inspector = sa.inspect(db.get_bind())
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    return {
        "migration_version": result[0] if result else None,
        "otp_columns_exist": 'otp_hash' in columns and 'otp_expires_at' in columns
    }
```

### 2. Add Startup Validation
```python
# backend/main.py startup event
@app.on_event("startup")
async def validate_schema():
    db = SessionLocal()
    try:
        # Check OTP columns exist
        inspector = sa.inspect(db.get_bind())
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'otp_hash' not in columns or 'otp_expires_at' not in columns:
            logger.critical("❌ FATAL: OTP columns missing from users table")
            raise RuntimeError("Database schema is out of date")
    finally:
        db.close()
```

### 3. Monitor Render Webhooks
- Set up Slack/email notification for failed deploys
- Monitor Render "Events" tab daily
- Verify commit hashes after each push

---

## EXECUTIVE SUMMARY

**Current Status:** 🔴 PRODUCTION FAILURE

**Issue:** /auth/register returns HTTP 500 on live Render

**Root Cause (SUSPECTED):** Render is running stale container or migrations didn't execute

**Immediate Action Required:**
1. Check Render dashboard for commit hash
2. If not `9a7184c` → Force clean rebuild
3. If is `9a7184c` → Check container shell for OTP columns
4. Apply remediation plan based on findings

**Time to Resolution:** 15-30 minutes (depending on rebuild time)

**Data Loss Risk:** ❌ NONE (if using Plan A or B)

**Confidence Level:** HIGH (fix is correct, just needs to reach production)

---

**NEXT STEPS:**
1. Access Render dashboard immediately
2. Follow diagnostic steps in Section 3
3. Execute remediation plan from Section 5
4. Complete verification checklist in Section 7
5. Report results using template in Section 8
