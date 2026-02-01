# App Store Readiness — Internal Checklist

This document summarizes important points for App Store / Play Store readiness specific to the Zeusonic beta release.

- Data usage
  - Audio uploaded by users is stored temporarily for processing and may be downloaded if a plan allows. No third-party sharing occurs without explicit consent.
  - We do not claim to train models on user-uploaded data or keep it beyond processing/retention windows.

- Payments
  - No payments are collected during Beta. Billing models are implemented server-side but not active for processing payments in beta.

- Beta indicator
  - `beta_mode` is a UI-only flag exposed via `GET /api/v1/meta` and rendered as a non-gated "Beta" badge. It does not change entitlements or features.

- No hidden features
  - All features in Beta are visible and explained to reviewers as necessary. Admin/dev endpoints are dev-only and blocked in production.

- Safe language
  - Use calm, non-promising language in screenshots and store listing to avoid implying final feature set.

