# 🚀 ZEUSONIC 1.0 TESTING CHECKLIST

**Release:** v1.0 (Closed Testing)  
**Date:** 2 February 2026  
**Status:** Ready for Private Beta  

---

## 📋 QUICK START

### Prerequisites

Ensure you have:
- [ ] Python 3.8+ installed
- [ ] Resend account with verified domain
- [ ] API keys configured in environment
- [ ] SQLite available (local development)

### First-Time Setup

```bash
# Clone/download Zeusonic
cd zeusonic

# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables (CRITICAL)
export JWT_SECRET=generate-a-random-32-char-string-here
export RESEND_API_KEY=re_your_actual_key_from_resend_dashboard
export STRIPE_SECRET_KEY=sk_test_your_test_key

# Run readiness check
python3 scripts/launch_readiness_check.py

# Start the backend
python -m uvicorn backend.main:app --reload --port 8000
```

---

## ✅ PRE-LAUNCH VERIFICATION (30 minutes)

### 1. Environment Readiness

- [ ] Run `python3 scripts/launch_readiness_check.py`
  - **Expected:** All checks pass or warnings only
  - **If failed:** Fix issues before proceeding

- [ ] Verify environment variables
  ```bash
  echo "JWT_SECRET: $(echo $JWT_SECRET | cut -c1-4)... (length: ${#JWT_SECRET})"
  echo "RESEND_API_KEY: $(echo $RESEND_API_KEY | cut -c1-4)... (length: ${#RESEND_API_KEY})"
  ```
  - **Expected:** Both set and reasonable lengths

### 2. Email Delivery Readiness

- [ ] Validate email configuration
  ```bash
  python3 scripts/validate_email_delivery.py
  ```
  - **Expected:** All checks pass (API connectivity OK)

- [ ] Test email send (optional)
  ```bash
  python3 scripts/validate_email_delivery.py --test-send
  ```
  - **Expected:** Email sent successfully (check logs)

### 3. Backend Startup

- [ ] Start backend server
  ```bash
  python -m uvicorn backend.main:app --reload --port 8000
  ```
  - **Expected output:**
    ```
    INFO:     Uvicorn running on http://127.0.0.1:8000
    INFO:     Application startup: JWT_SECRET configured
    INFO:     Database tables initialized
    ```
  - **If error:** Check JWT_SECRET is set

- [ ] Test health check
  ```bash
  curl http://localhost:8000/health
  ```
  - **Expected response:**
    ```json
    {
      "status": "ok",
      "db": "ok",
      "storage": "ok",
      "env": "development"
    }
    ```

### 4. Initial API Check

- [ ] List available endpoints
  ```bash
  curl http://localhost:8000/docs
  ```
  - **Expected:** Swagger UI loads with all auth endpoints visible

---

## 🔐 AUTHENTICATION TESTING (45 minutes)

### Test 1: User Registration with OTP

**Scenario:** New user signs up and receives OTP email

```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'
```

**Expected Response:**
```json
{
  "email": "test@example.com",
  "is_verified": false,
  "message": "Verification code sent to test@example.com. Check your inbox."
}
```

**Verification:**
- [ ] Response status: 201 Created
- [ ] User not verified yet (`is_verified: false`)
- [ ] Message indicates email sent
- [ ] Check Resend dashboard: Email sent log appears
- [ ] Check inbox: Received email with OTP code (6 digits)

---

### Test 2: OTP Email Content Check

**Expected email should contain:**
- [ ] Subject: "Your Zeusonic verification code"
- [ ] From: "Zeusonic <no-reply@zeustechafrica.com>"
- [ ] Body includes large, clear OTP code
- [ ] Expiry notice: "expires in 10 minutes"
- [ ] Security message: "If you did not request this, ignore"

**Important:** Copy the OTP code for Test 3

---

### Test 3: OTP Verification

**Scenario:** User verifies OTP from email

```bash
# Verify OTP (replace with actual OTP from email)
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp": "123456"
  }'
```

**Expected Response:**
```json
{
  "message": "Email verified successfully"
}
```

**Verification:**
- [ ] Response status: 200 OK
- [ ] Message indicates success
- [ ] Try with wrong OTP: Should fail with "Invalid code"
- [ ] Try after 10 minutes: Should fail with "Code expired"

---

### Test 4: User Login

**Scenario:** Verified user logs in and receives JWT token

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Verification:**
- [ ] Response status: 200 OK
- [ ] `access_token` is a valid JWT (starts with `eyJ`)
- [ ] `token_type` is "bearer"
- [ ] `expires_in` is 3600 seconds (60 minutes)

---

### Test 5: Unverified User Cannot Login

**Scenario:** User tries to login before email verification

```bash
# Register new user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "unverified@example.com",
    "password": "SecurePassword123!"
  }'

# Try to login without verifying OTP
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "unverified@example.com",
    "password": "SecurePassword123!"
  }'
```

**Expected Response:**
```json
{
  "detail": "Email not verified. Please verify your email first."
}
```

**Verification:**
- [ ] Response status: 403 Forbidden
- [ ] Error message is clear and actionable
- [ ] User must verify OTP before login

---

### Test 6: Duplicate Registration Prevention

**Scenario:** Same email cannot register twice

```bash
# Try to register same email twice
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "DifferentPassword456!"
  }'
```

**Expected Response:**
```json
{
  "detail": "Email already registered"
}
```

**Verification:**
- [ ] Response status: 409 Conflict
- [ ] Error message prevents user enumeration
- [ ] First user's account unaffected

---

### Test 7: Invalid Credentials

**Scenario:** Wrong password is rejected

```bash
# Login with wrong password
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "WrongPassword123!"
  }'
```

**Expected Response:**
```json
{
  "detail": "Invalid credentials"
}
```

**Verification:**
- [ ] Response status: 401 Unauthorized
- [ ] Error message is generic (no user enumeration)
- [ ] Legitimate user's account unaffected

---

## 📊 ERROR HANDLING TESTS (15 minutes)

### Test 8: Missing Required Fields

```bash
# Register with missing email
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "password": "SecurePassword123!"
  }'
```

**Expected Response:**
```json
{
  "detail": "Invalid request"
}
```

**Verification:**
- [ ] Response status: 422 Unprocessable Entity
- [ ] No stack trace returned
- [ ] Error is user-friendly

---

### Test 9: Invalid Email Format

```bash
# Register with invalid email
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "not-an-email",
    "password": "SecurePassword123!"
  }'
```

**Expected Response:**
```json
{
  "detail": "Invalid request"
}
```

**Verification:**
- [ ] Response status: 422 Unprocessable Entity
- [ ] No technical details leaked

---

### Test 10: Weak Password

```bash
# Register with password < 8 chars
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test2@example.com",
    "password": "short"
  }'
```

**Expected Response:**
```json
{
  "detail": "Invalid request"
}
```

**Verification:**
- [ ] Response status: 422 Unprocessable Entity
- [ ] Minimum 8-character requirement enforced

---

## 🛡️ SECURITY TESTS (10 minutes)

### Test 11: No OTP in API Response

**Verify:** Registering doesn't return OTP in response

- [ ] Response from `/auth/register` has NO `otp` field
- [ ] Response from `/auth/register` has NO `otp_hash` field
- [ ] OTP only sent via email, never in API

---

### Test 12: OTP Expires After 10 Minutes

**Manual test:**
1. [ ] Register user, receive OTP
2. [ ] Wait 10+ minutes
3. [ ] Try to verify OTP
4. [ ] Expected: "Verification code expired" error

---

### Test 13: JWT Token Verified

**Verify JWT structure:**

```bash
# From login response, decode token
python3 << 'EOF'
import base64
import json

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # From login response
parts = token.split('.')
payload = json.loads(base64.urlsafe_b64decode(parts[1] + '==='))
print(json.dumps(payload, indent=2))
EOF
```

**Expected output:**
```json
{
  "sub": "test@example.com",
  "exp": 1675336800
}
```

**Verification:**
- [ ] Token contains `sub` (user email)
- [ ] Token contains `exp` (expiry timestamp)
- [ ] Token uses HS256 algorithm (correct)

---

### Test 14: Server Doesn't Log Secrets

**Monitor logs while testing:**

```bash
# Watch logs (in separate terminal)
tail -f /var/log/zeusonic.log  # or stdout if running in terminal

# Run registration in other terminal
curl -X POST http://localhost:8000/auth/register ...
```

**Verification:**
- [ ] Logs show email (example@gmail.com) - OK
- [ ] Logs do NOT show OTP values
- [ ] Logs do NOT show passwords
- [ ] Logs do NOT show API keys
- [ ] Logs are readable with timestamps

---

## 📧 EMAIL RESILIENCE (Optional, 20 minutes)

### Test 15: Email Delivery Failure Handling

**Simulate Resend API key issue:**

```bash
# Temporarily remove RESEND_API_KEY
unset RESEND_API_KEY

# Try to register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test3@example.com",
    "password": "SecurePassword123!"
  }'

# Restore API key
export RESEND_API_KEY=re_your_key
```

**Expected Behavior:**
- [ ] Registration succeeds (user created)
- [ ] Warning logged: "Failed to send OTP email"
- [ ] User cannot verify (no email received)
- [ ] System remains stable (no crash)

**Verification:**
- [ ] User exists in database (can try login with wrong OTP)
- [ ] Server continues running
- [ ] Clear error in logs (no stack trace)

---

## 🎯 COMPLETE AUTH FLOW TEST (10 minutes)

### Test 16: Golden Path (Full Flow)

**Run automated test:**

```bash
python3 scripts/golden_path_auth.py
```

**Expected output:**
```
✅ API Health Check: PASS
✅ User Registration: PASS
✅ OTP Received: Check email for code
⏳ Waiting for OTP input...
(Enter OTP from email when prompted)
✅ OTP Verification: PASS
✅ User Login: PASS
✅ Create Project: PASS
✅ List Projects: PASS
🎉 ALL TESTS PASSED!
```

**Verification:**
- [ ] All 7 test steps pass
- [ ] Takes < 30 seconds (excluding user input)
- [ ] No errors or warnings
- [ ] Clear pass/fail for each step

---

## 📋 DATABASE CHECKS (Optional, 10 minutes)

### Test 17: User Data Integrity

**Query database directly:**

```bash
python3 << 'EOF'
import sqlite3

db = sqlite3.connect("backend/storage/zeusonic.db")
cursor = db.cursor()

# Check user exists
cursor.execute("SELECT email, is_verified, otp_hash, otp_expires_at FROM users WHERE email='test@example.com'")
user = cursor.fetchone()

if user:
    email, is_verified, otp_hash, expires = user
    print(f"Email: {email}")
    print(f"Verified: {is_verified}")
    print(f"OTP Hash: {otp_hash is not None}")
    print(f"OTP Expires: {expires}")
else:
    print("User not found")

db.close()
EOF
```

**Verification:**
- [ ] After registration: `is_verified = 0` (false)
- [ ] After OTP verify: `is_verified = 1` (true)
- [ ] After verification: `otp_hash = NULL`, `otp_expires_at = NULL`
- [ ] No plaintext OTP stored

---

## 🔧 TROUBLESHOOTING

### Issue: Backend won't start

**Problem:** `RuntimeError: JWT_SECRET is required but not configured`

**Solution:**
```bash
export JWT_SECRET=your-32-character-random-string-here
python -m uvicorn backend.main:app --reload
```

---

### Issue: Email not sent

**Problem:** Registration succeeds but no email received

**Checklist:**
- [ ] `RESEND_API_KEY` is set and valid
- [ ] Check Resend dashboard: Is domain verified?
- [ ] Run: `python3 scripts/validate_email_delivery.py`
- [ ] Check spam folder
- [ ] Verify recipient email is correct

---

### Issue: OTP verification fails

**Problem:** "Invalid verification code" even with correct OTP

**Checklist:**
- [ ] Copy OTP carefully (no spaces)
- [ ] OTP is 6 digits
- [ ] Less than 10 minutes since registration
- [ ] Correct email in request
- [ ] Database has user (check Test 17)

---

### Issue: Login fails after verification

**Problem:** User verified but login returns "Invalid credentials"

**Checklist:**
- [ ] Correct email spelling
- [ ] Correct password (passwords are case-sensitive)
- [ ] User is verified: `is_verified = 1` in database
- [ ] User exists: Check database directly

---

## 📝 SIGN-OFF

After completing all tests, sign off:

**Tester Name:** ___________________  
**Date:** ___________________  
**Environment:** (dev/test/staging)  
**Python Version:** ___________________  

### Test Results

| Category | Status | Notes |
|----------|--------|-------|
| Pre-Launch | ✅/⚠️/❌ | |
| Authentication | ✅/⚠️/❌ | |
| Error Handling | ✅/⚠️/❌ | |
| Security | ✅/⚠️/❌ | |
| Email Delivery | ✅/⚠️/❌ | |
| Complete Flow | ✅/⚠️/❌ | |

### Known Issues Found

1. _________________
2. _________________
3. _________________

### Recommendation

- [ ] **GO** - Ready for further testing
- [ ] **GO WITH CAVEATS** - Ready with known issues documented
- [ ] **NO-GO** - Blockers must be fixed

---

## 📚 ADDITIONAL RESOURCES

- [Zeusonic API Docs](http://localhost:8000/docs) - Swagger UI
- [ENVIRONMENT_CHECKLIST.md](../ENVIRONMENT_CHECKLIST.md) - Configuration audit
- [AUTH_SECURITY_REPORT.md](../AUTH_SECURITY_REPORT.md) - Security review
- [ERROR_HANDLING_GUIDE.md](../ERROR_HANDLING_GUIDE.md) - Error standards

---

## 🎯 TESTING DURATION

- **Quick validation (30 min):** Tests 1-4 + health check
- **Standard testing (2 hours):** Tests 1-14 + complete flow
- **Comprehensive testing (4 hours):** All tests + database checks + troubleshooting
- **Continuous testing:** Run golden path daily during testing phase

---

**Version:** 1.0  
**Last Updated:** 2 February 2026  
**Next Review:** After first round of tester feedback
