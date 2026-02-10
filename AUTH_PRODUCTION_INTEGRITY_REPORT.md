# AUTH PRODUCTION INTEGRITY REPORT

Date: 2026-02-10

## Summary
A limited auth re-open was performed to harden user selection and add temporary safe forensics to diagnose production 401s after OTP verification.

## What Was Detected
- Code review confirmed login previously used `.first()` with case-sensitive match on `users.email`.
- This can select an ambiguous record if duplicates exist (case variants or multiple rows).

## Integrity Checks (Read-Only)
- Duplicate email report script: [scripts/report_duplicate_users.py](scripts/report_duplicate_users.py)
- Local run result: **No duplicate emails found**.
- Production detection requires operator execution with production DB access.

## Changes Applied (Safe, Scoped)
- Login query now uses `LOWER(users.email) == email` and `.one_or_none()`.
- If multiple rows exist, login returns **500 Account integrity error** (prevents ambiguous selection).
- Temporary forensics log added before password verification:
  - user.id, normalized email, is_verified, hash prefix (first 8 chars), number of matching rows.

## Why Login Can Fail With Correct Hashing
If production contains duplicate users for the same email (case-insensitive), `.first()` may select a non-matching record. This yields 401 even when the correct password is provided. The new guard prevents this and surfaces an integrity error for remediation.

## Recommendation
- Run [scripts/report_duplicate_users.py](scripts/report_duplicate_users.py) against production DB.
- If duplicates exist, propose a controlled repair plan (keep most recent verified user; archive/delete others). Do not execute without approval.

## Status
Temporary forensics and defensive query hardening are in place. Auth behavior is unchanged unless corruption exists.
