# DEV AUTH MODE (TEMPORARY)

## Purpose
Enable password‑only registration/login for internal testing of the Zeusonic AI music transformation pipeline in production‑like environments.

## How It Works
- `AUTH_MODE=DEV` (backend) creates users immediately on `/auth/register`, sets `is_verified=true`, and skips OTP.
- `/auth/verify-otp` returns 410 "OTP disabled in DEV mode".
- Login uses the same hashing/JWT logic; no changes to protected route guards.
- Frontend reads `NEXT_PUBLIC_AUTH_MODE=DEV` to hide OTP UI and update registration copy.

## How to Disable (Return to PROD)
1. Set `AUTH_MODE=PROD` (or unset) in backend environment.
2. Set `NEXT_PUBLIC_AUTH_MODE=PROD` (or unset) in Vercel.
3. Deploy.

## Checklist Before Zeusonic 1.1 Public Launch
- Remove DEV auth code paths in [backend/api/auth.py](backend/api/auth.py).
- Remove DEV auth UI handling in [frontend/app/auth/register/page.tsx](frontend/app/auth/register/page.tsx) and [frontend/app/auth/verify/page.tsx](frontend/app/auth/verify/page.tsx).
- Remove this file.
- Confirm OTP flow and verification required in production.
