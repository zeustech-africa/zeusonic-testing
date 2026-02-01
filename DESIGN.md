ZEUSONIC Design System

Overview
--------
This document defines a minimal, professional design system for the Zeusonic product: a luxury, music-first interface inspired by Udio's layout & flow. This spec is intentionally lightweight to help frontend teams move quickly while preserving a consistent, high-quality visual language.

1. Color Palette
-----------------
Primary tone: Dark / deep charcoal base for a premium, stage-like canvas.

- Base / Dark: #0F1115 (very dark charcoal)
- Surface: #141619 (slightly lighter for panels)
- Accent 1 (Electric Blue): #4EA8FF (primary action, highlights)
- Accent 2 (Magenta Glow): #FF6EC7 (secondary accents, subtle glows)
- Muted Text: #A9B1BB
- On-Accent (Light): #FFFFFF

Usage
- Use Base for background, Surface for cards and nav.
- Accent 1 for primary CTAs and highlights. Use Accent 2 for secondary emphasis and soft glows.
- Keep contrast high for legibility.

2. Typography
--------------
Recommendations (web-safe + modern stack):
- Headings: Inter (or similar geometric sans: Product Sans / Poppins) - weights: 600, 700
- Body: Inter / system-ui - weights: 400, 500
- UI / labels: Inter 500 (caps for micro labels optional)

Scale
- H1: 48px/56
- H2: 32px/40
- H3: 24px/32
- Body: 16px/24
- Small: 12px/16

3. Spacing & Layout
--------------------
- Base spacing unit: 8px
- Components use multiples (8, 12, 16, 24, 32, 48)
- Max content width (center column): 1200px for landing; wide hero can go edge-to-edge.

4. Radius, Shadow & Glow
-------------------------
- Border radius: 8px for cards, 6px for buttons, 9999px for pills
- Shadow (soft): 0 8px 24px rgba(0,0,0,0.45)
- Glow: Use subtle outer glows on active controls with accent color at low opacity (e.g., 0 0 12px rgba(78,168,255,0.12))

5. Buttons & Controls
----------------------
Primary Button (Solid):
- Background: Accent 1 (#4EA8FF)
- Text: White
- Padding: 12px 20px
- Radius: 6px

Secondary Button (Ghost):
- Border: 1px solid rgba(255,255,255,0.06) or Accent 2 for emphasis
- Background: transparent
- Text: Accent 1 or white

Disabled: lower opacity (0.5) and not interactive

6. Udio-inspired patterns
--------------------------
- Hero: Large centered hero with headline, subline, and CTA buttons. Background: dark stage with subtle gradient and soft glow.
- Centered CTA: Place a main action ("Upload & Analyze") in hero and again in the dashboard primary area.
- Waveform visuals: Use SVG or Canvas-based waveforms in the dashboard; use a muted accent stroke and glow on hover.

7. Accessibility
-----------------
- Maintain 4.5:1 contrast for body text against background where possible.
- Buttons and inputs must be keyboard reachable and have visible focus outlines (use glow or outline).
- Provide alt text for logos and images.

Notes
-----
This system is intentionally modest and flexible. Implementation details (fonts, exact tokens) can be replaced by design system tooling (Tailwind tokens or CSS variables) later.
