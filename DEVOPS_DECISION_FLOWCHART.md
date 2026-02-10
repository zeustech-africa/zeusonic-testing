# DEVOPS DIAGNOSTIC DECISION FLOWCHART
**Quick Reference for Root Cause Identification**

---

## DECISION TREE

```
START: Is HTTP 404 on all endpoints?
│
├─ YES → Continue to Q2
│
└─ NO → Some endpoints return 200 or 500
   └─ FINDING: Service IS deployed and running
      └─ Go to SCENARIO: Service Running But Errors
```

---

```
Q2: Is the service visible in Render dashboard?
│
├─ NO → Service doesn't exist
│   └─ Go to REMEDY: Service Not Created
│
└─ YES → Service exists
   └─ Continue to Q3
```

---

```
Q3: What is the service status indicator?
│
├─ GREEN "Live" → Service should be running
│   └─ Continue to Q4
│
├─ RED "Build Failed" → Most recent deploy failed
│   └─ Go to REMEDY: Build Failed
│
├─ GRAY "Suspended" → Service is paused
│   └─ Go to REMEDY: Service Suspended
│
└─ BLUE "Building" → Currently deploying
   └─ WAIT and retry tests in 2-3 minutes
```

---

```
Q4: Is commit 9a7184c in the deployment history?
│
├─ NO → Old commit is deployed
│   └─ Go to REMEDY: Old Commit Deployed
│
├─ YES with FAILED → Commit failed to deploy
│   └─ Go to REMEDY: Build Failed
│
└─ YES with SUCCESS → Correct commit is deployed
   └─ Continue to Q5
```

---

```
Q5: Do the logs show startup errors?
│
├─ NO → Clean startup, but still 404?
│   └─ FINDING: Service running but routes unreachable
│      └─ Go to REMEDY: Service Routes Missing
│
└─ YES → Errors found during startup
   └─ Go to REMEDY: Startup Failed
```

---

## REMEDIATION PATHS

---

### REMEDY: Service Not Created
**Problem:** Service is not visible in Render dashboard

**Root Cause:** Either service was never created, or was deleted

**Solution Steps:**
1. Go to Render Dashboard: https://dashboard.render.com
2. Click "New +" button
3. Select "Web Service"
4. Connect GitHub repo (zeusonic)
5. Choose "Blueprint" option
6. Select the `render.yaml` file
7. Click "Create Web Service"
8. Wait for build to complete (3-5 minutes)
9. Test endpoint after deployment

**Time to Fix:** 5-10 minutes

---

### REMEDY: Service Suspended
**Problem:** Service status shows GRAY "Suspended"

**Root Cause:** Render auto-suspended service (free tier sleep) or manual suspension

**Solution Steps:**
1. In Render dashboard, find the service
2. Look for "Resume" button or similar
3. Click "Resume"
4. Wait 30 seconds for service to wake up
5. Test endpoint

**Time to Fix:** 1 minute

---

### REMEDY: Build Failed
**Problem:** Service status shows RED "Build Failed" or deployment with FAILED status

**Root Cause:** Docker build error, missing dependencies, or invalid configuration

**Solution Steps:**
1. In Render dashboard, go to service detail
2. Click "Events" tab
3. Find the failed deployment
4. Click to view full build logs
5. Search for "ERROR" or first occurrence of error
6. Look for:
   - Docker layer failures
   - Dependency installation failures
   - Configuration errors
7. **DO NOT MODIFY CODE** - Report error details
8. Once issue identified, fix locally:
   - Test locally: `docker build -t zeusonic .`
   - Commit fix: `git add . && git commit -m "fix: [issue]"`
   - Push: `git push origin main`
9. Render will auto-redeploy (if auto-deploy enabled)
10. Monitor Events tab for new deployment

**Time to Fix:** 10-15 minutes (depends on error severity)

---

### REMEDY: Old Commit Deployed
**Problem:** Deployment history shows older commit, not 9a7184c

**Root Cause:** 
- Auto-deploy was disabled
- Webhook failed
- Manual deployment was last used

**Solution Steps (Option A: Force Redeploy):**
1. In Render dashboard, go to service detail
2. Look for "Manual Deploy" button or "Redeploy" option
3. Choose "Deploy commit: 9a7184c"
4. Wait for deployment (3-5 minutes)
5. Monitor Events tab for completion
6. Test endpoint after success

**Solution Steps (Option B: Check Git):**
1. Verify commit 9a7184c exists locally:
   ```bash
   git log --oneline | grep 9a7184c
   ```
2. Verify it's on main branch:
   ```bash
   git branch -a --contains 9a7184c
   ```
3. If on main, ensure auto-deploy is enabled in Render
4. If not on main, merge to main:
   ```bash
   git merge 9a7184c
   git push origin main
   ```
5. Render will auto-deploy

**Time to Fix:** 5-10 minutes

---

### REMEDY: Startup Failed
**Problem:** Logs show errors during container startup

**Root Cause:** Depends on error - could be:
- Uvicorn won't start
- Database connection failed
- Alembic migration failed
- Missing environment variables
- Port binding issue

**Solution Steps:**
1. Get the exact error from logs
2. Search for error message in codebase
3. Common errors:
   - `Address already in use` → PORT conflict
   - `Connection refused` → Database unavailable
   - `No module named` → Missing dependency
   - `ModuleNotFoundError` → Import error
4. Once identified, fix locally
5. Test: Run locally with same config
   ```bash
   PORT=8000 uvicorn backend.main:app
   ```
6. Verify fix works
7. Commit and push
8. Monitor Render redeploy

**Time to Fix:** 10-20 minutes (depends on error complexity)

---

### REMEDY: Service Routes Missing
**Problem:** Service appears to start but all endpoints return 404

**Root Cause:** Most likely:
- FastAPI app not loading routes correctly
- Missing route definitions
- Incorrect import paths
- Application initialization failed silently

**Solution Steps:**
1. Verify locally that endpoints work:
   ```bash
   python3 -m uvicorn backend.main:app --reload
   curl http://localhost:8000/docs
   curl http://localhost:8000/health
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test123!"}'
   ```
2. If working locally, issue is with container setup
3. Check Dockerfile:
   - Working directory correct? (`WORKDIR /app`)
   - Dependencies installed? (`pip install -r requirements.txt`)
   - Start command correct?
4. Test Docker build locally:
   ```bash
   docker build -t zeusonic-test .
   docker run -p 8000:8000 zeusonic-test
   curl http://localhost:8000/docs
   ```
5. If all tests pass locally, push and let Render rebuild
6. May need to clear Render build cache

**Time to Fix:** 15-25 minutes

---

### REMEDY: Service Running But Errors
**Problem:** Some endpoints work (200) but others fail (500)

**Root Cause:** Application error - code issue, not deployment issue

**Solution Steps:**
1. Check logs for error stack trace
2. Identify which endpoint is failing
3. Look at endpoint code
4. Common issues:
   - Database query error
   - ORM field mismatch
   - Missing migration
   - Type validation error
5. This requires code debugging
6. Test endpoint locally to reproduce error
7. Fix code
8. Verify locally
9. Push and redeploy
10. Monitor logs for error stack trace

**Time to Fix:** 20-40 minutes (depends on error complexity)

---

## QUICK DECISION MATRIX

| Finding | Root Cause | Remedy | Time |
|---------|-----------|--------|------|
| Service not in dashboard | Never created | Create via blueprint | 5 min |
| Status: Suspended | Auto-paused or manual | Click Resume | 1 min |
| Status: Build Failed | Build error | Check logs, fix, redeploy | 10 min |
| Status: Live, but 404 | Old commit deployed | Manual deploy of 9a7184c | 5 min |
| Status: Live, but logs show errors | Startup error | Fix error, commit, redeploy | 15 min |
| All endpoints return 404 | Routes not loading | Debug container, rebuild | 20 min |
| Some endpoints return 200, others 500 | Application error | Debug code, fix, redeploy | 30 min |

---

## EXECUTION SEQUENCE

### Phase 1: Information Gathering (10 minutes)
1. ✓ Follow RENDER_NAVIGATION_GUIDE.md
2. ✓ Record all service details
3. ✓ Run endpoint tests: `bash render_diagnostic_tests.sh`
4. ✓ Fill DIAGNOSTIC_DATA_SUBMISSION_FORM.md

### Phase 2: Diagnosis (5 minutes)
1. ✓ Follow decision tree above
2. ✓ Identify root cause
3. ✓ Locate matching REMEDY section

### Phase 3: Remediation (5-30 minutes, depends on issue)
1. ✓ Follow steps in matching REMEDY
2. ✓ Execute fix
3. ✓ Verify deployment
4. ✓ Test endpoints

### Phase 4: Verification (5 minutes)
1. ✓ Run `bash render_diagnostic_tests.sh` again
2. ✓ Verify 200 responses on key endpoints
3. ✓ Test registration flow end-to-end

---

## CRITICAL POINTS

**Do NOT:**
- ❌ Modify code without clear evidence of code issue
- ❌ Redeploy blindly without diagnosis
- ❌ Reset disks without exhausting all other options
- ❌ Assume the error is the same as before without verifying

**DO:**
- ✅ Follow decision tree systematically
- ✅ Gather complete diagnostic data first
- ✅ Identify root cause before acting
- ✅ Test locally if modifying code
- ✅ Verify fix with endpoint tests

---

## NEXT STEP

1. Open RENDER_NAVIGATION_GUIDE.md
2. Follow all steps to gather diagnostic data
3. Fill DIAGNOSTIC_DATA_SUBMISSION_FORM.md completely
4. Return with filled form
5. I will use decision tree above to diagnose and remediate
