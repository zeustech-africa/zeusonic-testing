# UI Delivery Checklist

This document summarizes the UI system delivered and quick validation steps for QA / Beta.

Key features delivered
- Centralized design tokens: `design-tokens.json`
- Global CSS variables and utilities: `styles/globals.css`
- UDIO-inspired layout: `studio-grid`, `left-rail`, `center-canvas`, `right-panel` with mobile collapse (`mobile-bottom-nav`, `fab`)
- Subscription visual hierarchy: `tier-free`, `tier-creator`, `tier-pro` classes and `SubscriptionAura` client helper
- Components refactored to use design system:
  - Header / AppLayout
  - `SubscriptionBadge` (consumes `/api/v1/subscription`)
  - `AudioUploadPanel` (uses entitlements and shows `Upgrade to unlock` CTA)
  - `Timeline` / waveform container
  - `Button` variants: `primary`, `secondary`, `upgrade`, `ghost`

QA steps
1. Run frontend locally: `cd frontend && npm install && npm run dev`
2. Start backend on `localhost:8001` and login to obtain a JWT.
3. Visit `/dashboard` and confirm:
   - Left tool rail is visible on desktop
   - Center canvas shows upload panel and timeline
   - Right AI panel is present
4. Test subscription visuals:
   - No subscription: `SubscriptionBadge` shows `FREE` neutral
   - Use backend admin endpoint to set a `CREATOR` or `PRO` subscription and verify badge and aura glow update
5. On mobile (responsive view): verify bottom nav and FAB appear; touch controls are large and tappable.

Notes
- This delivery avoids any payment flows and focuses on entitlements and UI readiness for beta and app store submissions.
