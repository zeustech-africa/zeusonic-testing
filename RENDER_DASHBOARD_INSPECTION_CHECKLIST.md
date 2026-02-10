# RENDER DASHBOARD INSPECTION CHECKLIST
**DevOps Diagnostic Tool | Zeusonic Backend Service**

---

## TASK 1: SERVICE EXISTENCE VERIFICATION

### 1.1 Navigate to Render Dashboard
- [ ] Go to https://dashboard.render.com
- [ ] Log in with your credentials
- [ ] You should see your services list

### 1.2 Locate Backend Service
Look for a service with a name containing any of:
- [ ] `zeusonic-api`
- [ ] `zeusonic-backend`
- [ ] `zeusonic` (with -api or -backend suffix)
- [ ] Any service you remember creating

**RECORD: Service name found:** `_____________________`

### 1.3 Verify Service Type & Status
Click on the service to open its detail page. Record:

**Service Details:**
- [ ] Service Type (Web Service / Background Worker / Cron / Other): `___________________`
- [ ] Service Status (green/yellow/red):
  - [ ] **Live** (green) - service is running
  - [ ] **Build in Progress** (blue) - currently deploying
  - [ ] **Build Failed** (red) - most recent deploy failed
  - [ ] **Suspended** (gray) - service is paused
  - [ ] **Deleted** (not visible) - service was removed

**Record: Service Status:** `_____________________`

### 1.4 Verify Service URLs
In the service detail page, find the "Render URL" or "Public URL" section.

**Primary URL shown by Render:**
```
https://_______________________.onrender.com
```

**Secondary URLs (if any):**
```
https://_______________________.onrender.com
```

**Custom domains (if any):**
```
_____________________________
```

---

## TASK 2: DEPLOYMENT STATE AUDIT

### 2.1 Check GitHub Connection
In service settings, look for:
- [ ] **Repository:** (should show `owner/zeusonic`)
  - Repository: `_____________________________`
- [ ] **Branch:** (should show `main`)
  - Branch: `_____________________________`
- [ ] **Auto-Deploy:** (look for toggle)
  - [ ] **Enabled** (auto-deploys on git push)
  - [ ] **Disabled** (manual deploys only)

### 2.2 Check Deployment History
Click "Events" or "Deployments" tab. You should see a timeline of recent deploys.

**RECORD the most recent 3 deployments:**

**Deploy #1 (Most Recent):**
- Timestamp: `_____________________________`
- Commit Hash: `_____________________________`
- Status: [ ] Success [ ] Failed [ ] In Progress
- Duration: `_____________________________`

**Deploy #2:**
- Timestamp: `_____________________________`
- Commit Hash: `_____________________________`
- Status: [ ] Success [ ] Failed [ ] In Progress

**Deploy #3:**
- Timestamp: `_____________________________`
- Commit Hash: `_____________________________`
- Status: [ ] Success [ ] Failed [ ] In Progress

### 2.3 Verify Commit 9a7184c Was Deployed
Look through the deployment history:
- [ ] **Found:** Commit `9a7184c` was deployed ✅
  - When: `_____________________________`
  - Status: [ ] Success [ ] Failed
  
- [ ] **Not Found:** Commit `9a7184c` was NOT deployed ❌
  - Most recent deployed commit: `_____________________________`

---

## TASK 3: URL & ROUTING VALIDATION

### 3.1 Record the Correct Service URL
From Task 2.1, the primary Render URL is:
```
https://_______________________.onrender.com
```

### 3.2 Test Each Endpoint
Using the correct URL from 3.1, test these endpoints:

**Test 1: Root endpoint**
```bash
curl -v https://_______________________.onrender.com/
```
Expected: 404 (OK) or redirect
Actual: HTTP `_____`
Response body (first 100 chars): `_____________________________`

**Test 2: OpenAPI docs**
```bash
curl -v https://_______________________.onrender.com/docs
```
Expected: 200 (HTML page with Swagger UI)
Actual: HTTP `_____`
Response body (first 100 chars): `_____________________________`

**Test 3: OpenAPI schema**
```bash
curl -v https://_______________________.onrender.com/openapi.json
```
Expected: 200 (JSON with API schema)
Actual: HTTP `_____`
Response body (first 100 chars): `_____________________________`

**Test 4: Health check (if endpoint exists)**
```bash
curl -v https://_______________________.onrender.com/health
```
Expected: 200 or 404 (depends on if endpoint exists)
Actual: HTTP `_____`
Response body: `_____________________________`

**Test 5: Registration endpoint**
```bash
curl -v -X POST https://_______________________.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"diagnostic-test@example.com","password":"TestPass123!@#"}'
```
Expected: 422 (validation) or 400 (bad request) or 500 (error), NOT 404
Actual: HTTP `_____`
Response body: `_____________________________`

### 3.3 Determine 404 Source
Based on responses above:
- [ ] **All endpoints return 404** → 404 is from Render routing layer (service not reachable)
- [ ] **Some endpoints return 200** → Service is reachable, 404 is from FastAPI
- [ ] **/docs and /openapi.json work** → Service is running, specific routes missing

---

## TASK 4: RENDER SERVICE CONFIGURATION CHECK

### 4.1 Verify Runtime Configuration
In service settings, find "Environment":

- [ ] **Build Logs Available:** (click to expand)
  - [ ] Build succeeded
  - [ ] Build failed
  - Docker build output (first error): `_____________________________`

- [ ] **Start Command / Runtime Settings:**
  - Runtime: [ ] Docker [ ] Node/Python/Other
  - Start command shown: `_____________________________`

- [ ] **Environment Variables:**
  - PORT: `_____` (should be empty or 0, Render sets it)
  - DATABASE_URL: `_____________________________`
  - Other critical vars: `_____________________________`

### 4.2 Verify Health Check Settings
Look for "Health Check" section:
- [ ] Health check configured:
  - [ ] Path: `_____________________________`
  - [ ] Interval: `_____ seconds`
  - [ ] Timeout: `_____ seconds`
  - [ ] Status: [ ] Passing [ ] Failing [ ] Unknown

- [ ] No health check configured (OK for Docker services)

### 4.3 Check Port Binding
- [ ] Service binds to `$PORT` env variable (correct)
- [ ] Service binds to fixed port 8000 (risky)
- [ ] Port setting: `_____________________________`

---

## TASK 5: LOG & EVENT ANALYSIS

### 5.1 Access Render Logs
In service detail page, click "Logs" tab.

### 5.2 Check for Container Startup Errors
Look for the most recent startup sequence. Record:

**Container Start Time:**
- Timestamp: `_____________________________`
- Status: [ ] Started successfully [ ] Failed to start [ ] Crashed

**First 50 lines of logs (from startup):**
```
_____________________________
_____________________________
_____________________________
_____________________________
_____________________________
```

### 5.3 Search for Error Keywords
In the logs, search (Ctrl+F) for:
- [ ] "ERROR" - Found: [ ] Yes [ ] No
- [ ] "failed" - Found: [ ] Yes [ ] No
- [ ] "panic" - Found: [ ] Yes [ ] No
- [ ] "connection refused" - Found: [ ] Yes [ ] No
- [ ] "listen" - Found: [ ] Yes [ ] No (should see "listening on")
- [ ] "Uvicorn" - Found: [ ] Yes [ ] No (should see uvicorn startup)

**Critical errors found:**
```
_____________________________
_____________________________
_____________________________
```

### 5.4 Check Events Timeline
Click "Events" tab to see deployment timeline:
- [ ] Most recent event type: `_____________________________`
- [ ] Last 3 events:
  1. `_____________________________`
  2. `_____________________________`
  3. `_____________________________`

---

## TASK 6: SYNTHESIS & ROOT CAUSE

Based on all data collected, answer:

### Q1: Does the service exist?
- [ ] **YES** - Service found in dashboard
- [ ] **NO** - Service not found / deleted

### Q2: Is the service active?
- [ ] **YES** - Status is "Live"
- [ ] **NO** - Status is "Failed" or "Suspended"

### Q3: Is the correct commit deployed?
- [ ] **YES** - Commit 9a7184c is running
- [ ] **NO** - Different commit is deployed
- [ ] **UNKNOWN** - Can't determine from dashboard

### Q4: Is the service reachable?
- [ ] **YES** - At least /docs or /openapi.json returns 200
- [ ] **NO** - All endpoints return 404

### Q5: Are there build/startup errors?
- [ ] **YES** - Found errors in logs/events
  - Error summary: `_____________________________`
- [ ] **NO** - Logs show clean startup

### ROOT CAUSE ASSESSMENT
Based on answers above, the issue is:

- [ ] **Service doesn't exist** → Must create via render.yaml blueprint
- [ ] **Service is suspended** → Click Resume button
- [ ] **Service build failed** → Fix error and redeploy
- [ ] **Old commit deployed** → Force redeploy of correct commit
- [ ] **Service won't start** → Fix startup command or logs
- [ ] **Service not reachable** → Check port/routing configuration
- [ ] **Unknown** → Provide logs for analysis

---

## NEXT STEPS

Once you complete this checklist, provide:
1. All recorded values above
2. Screenshots of key dashboard sections (optional but helpful)
3. Full logs output if build/startup failed

Then I will:
1. Analyze findings
2. Identify exact root cause
3. Provide step-by-step remediation plan
4. Verify resolution

---

**IMPORTANT:** This checklist requires manual inspection of the Render dashboard. I cannot access it remotely, but once you gather this data, I can diagnose exactly what's wrong and provide the precise fix.
