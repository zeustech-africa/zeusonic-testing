# RENDER DASHBOARD NAVIGATION GUIDE
**Step-by-Step Instructions for DevOps Diagnosis**

---

## PHASE 1: ACCESS & LOCATE SERVICE

### Step 1: Open Render Dashboard
```
1. Go to https://dashboard.render.com
2. Click "Log In" if not already authenticated
3. You should see your account homepage with a list of services
```

### Step 2: Find Zeusonic Backend Service
```
On the main dashboard, you'll see a list of all your deployed services.
Look for:
  ✓ zeusonic-api
  ✓ zeusonic-backend
  ✓ zeusonic (followed by -api or -backend)
  ✓ Any service you remember creating recently

RECORD: The exact service name shown: _____________________
```

**If service is NOT visible:**
- [ ] Check if you're in the correct account
- [ ] Check if service was deleted
- [ ] It's possible the service was never created

**If service IS visible:**
- [ ] Click on the service name to open its detail page
- [ ] Continue to Step 3

---

## PHASE 2: VERIFY SERVICE CONFIGURATION

### Step 3: Check Service Status
**Location:** Top of service detail page

Look for a status indicator:
- **GREEN circle + "Live"** → Service is running ✓
- **RED circle + "Build Failed"** → Most recent deploy failed ✗
- **BLUE circle + "Building"** → Currently deploying
- **GRAY circle + "Suspended"** → Service is paused ✗
- **No service visible** → Service was deleted ✗

**Record:**
```
Status Indicator: _____________________
Status Text: _____________________
Last Updated: _____________________
```

**If status is RED, GRAY, or service is missing:**
- This explains the 404 errors
- Proceed to PHASE 3 for remediation

---

### Step 4: Get the Public Backend URL
**Location:** Service detail page, look for "Render URL" or "Public URL" section

You should see a URL like:
```
https://some-service-name.onrender.com
```

**Record this URL exactly:**
```
Backend URL: https://_____________________________.onrender.com
```

**This is the URL to use for all endpoint tests.**

---

### Step 5: Verify GitHub Connection
**Location:** Service Settings → Source Control

Look for:
- **Repository:** Should show `owner/zeusonic`
- **Branch:** Should show `main`
- **Auto-Deploy:** Should be enabled (green toggle)

**Record:**
```
Repository: _____________________
Branch: _____________________
Auto-Deploy: [ ] Enabled [ ] Disabled
```

---

## PHASE 3: CHECK DEPLOYMENT STATE

### Step 6: View Deployment History
**Location:** Service page → "Events" or "Deployments" tab

You should see a timeline of deployments like:
```
✓ 2 hours ago   - Commit abc123... - SUCCESS
✗ 4 hours ago   - Commit def456... - FAILED
✓ 1 day ago     - Commit ghi789... - SUCCESS
```

**Important:** Look for commit `9a7184c` in this list.

**Record the most recent 3 deployments:**

| # | Time | Commit Hash | Status |
|---|------|-------------|--------|
| 1 | _____ | _____________________________ | [ ] Success [ ] Failed |
| 2 | _____ | _____________________________ | [ ] Success [ ] Failed |
| 3 | _____ | _____________________________ | [ ] Success [ ] Failed |

**Critical Question:**
- Is commit `9a7184c` in the list? [ ] Yes [ ] No
- If yes, what is its status? [ ] Success [ ] Failed [ ] Not yet deployed

---

### Step 7: Check Latest Deploy Logs (if FAILED)
**Location:** Click on a failed deployment row → View logs

If the most recent deployment shows FAILED:
1. Click on it to expand
2. Look for error messages (usually in red text)
3. Common errors:
   - `Docker build failed`
   - `Dependency installation failed`
   - `Out of memory`
   - `Build timeout`

**Record any errors:**
```
Build Error: _____________________________
_____________________________
_____________________________
```

---

## PHASE 4: VERIFY SERVICE CONFIGURATION

### Step 8: Check Runtime Settings
**Location:** Service page → Settings (gear icon)

Look for "Environment" section with:

**Runtime Information:**
```
Language/Runtime: [ ] Docker [ ] Node [ ] Python [ ] Other
Dockerfile Path: _____________________
Build Command: _____________________
Start Command: _____________________
```

**Expected values:**
- Runtime: Docker
- Dockerfile Path: `./Dockerfile`
- Start Command: `sh -c "alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"`

---

### Step 9: Check Environment Variables
**Location:** Service Settings → Environment Variables section

You should see variables like:
- `PORT` (usually empty or pre-set by Render)
- `DATABASE_URL` (if using external DB)
- Custom variables you set

**Record critical variables:**
```
PORT: _____________________
DATABASE_URL: _____________________
Other vars: _____________________
```

---

### Step 10: Check Health Check (if configured)
**Location:** Service Settings → Health Check section

Health checks tell Render if your service is healthy:
- **Path:** `/health` or similar
- **Interval:** Usually 30 seconds
- **Status:** Passing / Failing / Unknown

**Record:**
```
Health Check Enabled: [ ] Yes [ ] No
Path: _____________________
Status: [ ] Passing [ ] Failing [ ] Unknown
```

---

## PHASE 5: ANALYZE LOGS

### Step 11: Access Service Logs
**Location:** Service page → "Logs" tab

This shows real-time output from your running container.

### Step 12: Look for Startup Sequence
Scroll to the bottom (oldest logs first). You should see something like:
```
[timestamp] Starting container...
[timestamp] Running startup command...
[timestamp] alembic: INFO Running upgrade 0007 -> 0008
[timestamp] Application startup complete
[timestamp] Uvicorn running on 0.0.0.0:8000
```

**Record startup sequence:**
```
Container started: [ ] Yes [ ] No (if no, service never started)
Alembic ran: [ ] Yes [ ] No
Uvicorn started: [ ] Yes [ ] No
Any errors: _____________________________
```

### Step 13: Search for Errors
Use your browser's Find function (Ctrl+F) to search the logs for:
- `ERROR` - Found: [ ] Yes [ ] No
- `failed` - Found: [ ] Yes [ ] No
- `Connection refused` - Found: [ ] Yes [ ] No
- `panic` - Found: [ ] Yes [ ] No

**If errors found:**
```
Error summary: _____________________________
_____________________________
```

---

## PHASE 6: CRITICAL DECISION POINT

### Step 14: Assess Service State

Based on information gathered, determine:

**Question 1: Does the service exist?**
- [ ] Yes, I can see it in the dashboard
- [ ] No, it's not in the service list
- [ ] Unknown

**Question 2: Is the service currently running?**
- [ ] Yes, status is "Live" (green)
- [ ] No, status is "Failed" or "Suspended"
- [ ] Unknown

**Question 3: Is commit 9a7184c deployed?**
- [ ] Yes, in deployment history with SUCCESS status
- [ ] No, it's not in the history
- [ ] Yes, but with FAILED status
- [ ] Unknown

**Question 4: Are there any error messages in logs?**
- [ ] Yes, startup errors found
- [ ] No, logs look clean
- [ ] Logs not accessible / empty

---

## NEXT ACTIONS

Once you complete this guide:

### What to provide me:
1. All filled-in recorded values above
2. Screenshot of service status page (top of dashboard)
3. Screenshot of deployment history (if available)
4. Screenshot of startup logs (if available)
5. Any error messages from logs

### I will then:
1. Analyze all collected data
2. Identify the exact root cause
3. Determine if issue is:
   - Service not deployed
   - Service deployed with wrong commit
   - Service crashed at startup
   - Service is suspended
   - Other configuration issue
4. Provide exact remediation steps

---

## QUICK REFERENCE: Where to Find Things

| Information | Location in Dashboard |
|-------------|----------------------|
| Service Status | Top of service page (Live/Failed/Suspended) |
| Public URL | Service detail page (Render URL section) |
| Deployment History | Events tab |
| Startup Logs | Logs tab |
| Configuration | Settings (gear icon) |
| Environment Variables | Settings → Environment Variables |
| Health Check Status | Settings → Health Check |
| Error Messages | Logs tab (search for ERROR/failed) |

---

**REMEMBER:** This diagnosis requires no code changes. You're purely gathering information about the deployment state. Do NOT modify anything until we determine the root cause.
