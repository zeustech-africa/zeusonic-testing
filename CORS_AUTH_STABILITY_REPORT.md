# CORS & Auth Stability Report

## Root Cause
Browser requests to auth endpoints failed due to CORS origin restrictions and missing `/auth/verify` alias. The backend only exposed `/auth/verify-otp`, while the client attempted `/auth/verify`, causing 404s in-browser that surfaced as network/CORS errors.

## Why It Failed Only in Browser
Browser-enforced CORS blocked requests from Vercel origins not explicitly allowed. CLI curl requests bypass CORS, so they appeared to work even when the browser failed.

## Changes Made
- CORS: ensured official Vercel origins are always allowed and disabled credentials (token-based auth).
- Added `/auth/verify` alias that calls the existing OTP verification logic.
- Added minimal logging for verify and login endpoints, including request origin.

## Proof of Success (Local)
- Verify endpoint:
  - Request: `POST /auth/verify` with Origin `https://zeusonic-t.vercel.app`
  - Response: `{"detail":"No verification code requested"}` (expected 400 JSON)
- Login endpoint:
  - Request: `POST /auth/login` with Origin `https://zeusonic-t.vercel.app`
  - Response: `{"detail":"Invalid credentials"}` (expected 401 JSON)

## Files Updated
- backend/main.py
- backend/api/auth.py

## Deployment Notes
- Render will auto-deploy the changes.
- Check logs for `[AUTH][OTP] Verify endpoint hit` and `[AUTH][LOGIN] Login endpoint hit` with the Origin header.
