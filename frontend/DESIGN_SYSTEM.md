# Zeusonic Design System

Purpose
- A compact, production-ready design system inspired by UDIO and tailored for Zeusonic. Provides tokens, layout rules, component patterns, and subscription visual hierarchies.

Color tokens
- Primary background: `--bg` — deep navy/black (#070812)
- Surface: `--surface` — slightly lighter panel surface (#0F1620)
- Accent / Neon Cyan: `--accent` — electric cyan highlight (#00C2FF)
- Electric / Cyan bright: `--electric` — interactive highlights (#00E6FF)
- Gold / Electric Yellow: `--gold` — premium plan accents (#FFD24A)
- Muted text: `--muted` — descriptive/helper text (#A9B1BB)
- Danger: `--danger` — errors (#FF6B6B)
- Success: `--success` — positive (#3CE6A1)
- Text: `--text` — primary text color (#E8F0F6)

Typography
- Sans: Inter stack (system fallback)
- Mono: ui-monospace for timeline/audio stamps
- Scale (CSS var based in `design-tokens.json`):
  - h1: 32px
  - h2: 24px
  - h3: 18px
  - body: 14px
  - mono: 13px

Spacing & Radii
- Spacing scale: 4px, 8px, 12px, 16px, 24px, 32px, 48px, 96px
- Border radius: 10px default, small 6px, pill for buttons

Shadows & Glow
- `shadow-soft`: deep, subtle panel shadow for depth
- `glow-cyan`: subtle cyan glow for Creator plan emphasis
- `glow-gold`: subtle gold glow & animation for Pro plan
- Glow usage: only for callouts (tier badges, upgrade CTAs), keep minimal and subtle

Layout principles (UDIO-inspired)
- Left tool rail (sticky): 220px width on desktop
- Central studio canvas (fluid): primary workspace, minimum height 420px
- Right AI parameter panel (sticky): 320px width on desktop
- Mobile: single-column layout with bottom navigation and a floating primary action button (FAB)

Subscription Visual Hierarchy
- FREE: neutral muted styling
- CREATOR: cyan/electric glow (`tier-creator`) used for subtle emphasis
- PRO: gold glow and a soft pulsing animation (`tier-pro`) marking premium status

Components
- `Button`: variants `primary`, `secondary`, `ghost`, `upgrade`, disabled state
- `Card`: surface container with `shadow-soft`
- `Heading`: uses tokenized sizes
- `SubscriptionBadge`: shows plan_code, visual tier styles, title tooltip
- `Timeline`: mono-font timeline container ready for waveform renderer

Accessibility & Interactions
- Disabled buttons are visible and `aria-disabled` is set.
- Locked features show a tooltip: "Upgrade to unlock" to inform users why action is disabled.
- All interactive controls have touch-friendly sizing on mobile.

Notes
- This design system is additive and non-breaking. Components consume tokens defined in `design-tokens.json` and globally available CSS variables in `styles/globals.css`.
- The visual language aims to be premium, calm, futuristic, and powerful — not playful nor generic.
