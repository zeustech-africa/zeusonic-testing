# Beta Launch Checklist

**Who gets access**
- Internal team + selected creators invited via API key provisioning.
- Access is manually controlled; keys can be revoked in the admin UI/dev tools.

**How to revoke access**
- Revoke or delete API key via database or admin tooling (dev-only admin endpoints exist for simulation).

**What success looks like (qualitative)**
- Creators can upload audio, receive processed results, and clearly understand next steps when gated.
- No crashes or unhandled exceptions during normal flows.
- Constructive feedback is collected from early creators.

**What to watch for**
- Crash reports and frequent 'Failed' job states.
- Repeated upgrade-gated complaints — look for confusing messaging.
- Any unexpected logging of sensitive keys or PII.

**Post-launch**
- Run a small cohort test (10–30 creators) and collect feedback via email.
- Iterate on helper copy and onboarding within two weeks.
