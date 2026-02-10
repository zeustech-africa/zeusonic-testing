Zeusonic Frontend (scaffold)

This is a minimal Next.js (App Router) + TypeScript scaffold aligned with the design system in the repository.

Quickstart (local dev)
1. cd frontend
2. npm install
3. npm run dev

Notes
- The design tokens are defined in `design-tokens.json` and consumed by `tailwind.config.js` (colors, typographic family, spacing, radii, shadows). The system adopts Zeusonic brand colors: gold, electric cyan, and deep navy to deliver a premium, futuristic feel.

- New components and classes:
  - `tier-creator` / `tier-pro` / `tier-free` — visual hierarchy for subscription tiers (glow and subtle animation for `PRO`).
  - `btn-upgrade` — prominent upgrade CTA style (gold gradient + glow)
  - `studio-grid`, `left-rail`, `center-canvas`, `right-panel` — UDIO-inspired layout helpers. Mobile collapses to a single column with `mobile-bottom-nav` and a floating `fab` primary action.
- Tailwind theme values are mapped from the tokens so components can use `bg-accent`, `text-muted`, `shadow-soft`, etc.
- The logo assets are in `public/assets/branding` and are used in the header.
- This scaffold supports a live upload integration for the `AudioUploadPanel` (used on `/generate` and `/dashboard`). For local dev, authenticate via the standard login flow to obtain a JWT. See `./docs/AUDIO_UPLOAD_PANEL.md` and `./docs/AUDIO_UPLOAD_PANEL_LIVE.md` for the AudioUploadPanel visual states, UI contract, and live integration details.

Storybook
- Storybook is configured for this project. To run it locally:
  1. cd frontend
  2. npm install
  3. npm run storybook
- Purpose: Storybook is the visual component workbench. Create and test components there before integrating into pages.
- Rule: All new components should include stories. See `frontend/.storybook` and `frontend/components/ui/*.stories.tsx`. Interactive/UX mock stories should be placed under `frontend/components/features/*` with a clear `interactive` or `/Interactive` identifier so designers can find them quickly.
- **Storybook Live integration:** For components that interface with backend workflows (like `AudioUploadPanel`), create a `Live` story that demonstrates real integration, but mock network calls inside the story so Storybook remains fast and deterministic.
- **Storybook Interaction Tests:** Interactive stories should include Play tests (Storybook `play` functions using `@storybook/testing-library`) to lock UX behavior and prevent regressions during refactor or API wiring.

Available UI primitives (frontend/components/ui):
- `Button` — variants: `primary` | `ghost`; sizes: `sm` | `md` | `lg`; supports `disabled` prop. Use for actions and CTAs.
- `Container` — layout wrapper providing `max-w-6xl` and horizontal padding.
- `Heading` — typographic headings (levels 1-3); use for titles and section headers.
- `Card` — surface container with rounded corners and `shadow-soft` for elevation.
- `Input` — form input for dark UI; supports `error` and `disabled` states; uses `focus:ring-accent`.
- `Badge` — small labels (variants: `accent` | `muted`) for statuses and tags.
- `Divider` — subtle horizontal rule using `border-surface`.

Application layout & page scaffolds
- AppLayout (components/AppLayout.tsx) is the page-level shell used by scaffold pages.
- Pages added (placeholders only): `/dashboard`, `/generate`, `/library` — each uses AppLayout and component primitives to establish the structure for future features.

Guidance:
- Compose pages from these primitives; avoid adding component-level styles unless necessary.
- Prefer token-based classes (e.g., `bg-accent`, `text-muted`) over direct hex values to maintain consistency.
- Rule: stabilize layout and components before adding feature logic.
