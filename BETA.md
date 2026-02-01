# Beta mode (beta_mode)

**What it is**

A simple, UI-only toggle exposed from the backend via `GET /api/v1/meta` as `beta_mode: true|false`.

**What it does NOT do**

- It does not change entitlements, features, or billing.
- It does not enable or gate functionality.
- It is not a feature flag for behavior changes.

**Why it exists**

- Provide clear UX during early access and app-store review by showing a non-intrusive "Beta" badge.
- Keep signaling purely informational and safe for store submission.

