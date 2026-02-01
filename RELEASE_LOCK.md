# Release Lock — Pre-store Submission Freeze

This document describes what must remain frozen prior to App Store / Google Play submission and what qualifies as emergency-only changes.

What is frozen
- UI layouts and core UX flows
- Billing and entitlement logic
- Feature flags (except production-only operational toggles like `disable_uploads`)
- Any backend changes that modify database migrations

What must NOT change before store submission
- Subscription or billing behavior and wording
- Pricing related language in frontend or metadata
- Any tracking or analytics SDK additions

Emergency-only changes
- Critical bug fixes that cause crashes or data loss
- Security fixes that address PII leakage or critical vulnerabilities

Rollback procedure
1. If a bad release is detected, open an urgent revert PR to the last green commit.
2. Notify the review team and pause store submission if necessary.
3. If a database migration was applied, follow the DB rollback notes included in the migration and coordinate a maintenance window.

