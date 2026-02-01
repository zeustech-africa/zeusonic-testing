Frontend Architecture Recommendation — Zeusonic

1) Recommended stack (proposal, no scaffolding yet)
- Framework: Next.js (React-based, SSR/SSG, great for performance and SEO)
- Styling: Tailwind CSS for utility-first, rapid layout and consistent tokens
- UI Kit: Headless UI (for accessible primitives) + custom components following DESIGN.md
- Asset handling: SVG for logos & icons; next/image for next-level optimization
- Why this fits Zeusonic:
  - Luxury music experience: needs fast, smooth UI with crisp visuals (Next + Tailwind is excellent for performant pages and polished design)
  - SEO-ready landing pages for discovery and marketing
  - Easy server-side rendering for social previews and better initial load

2) Data & API integration
- Use a small API client wrapper (axios or fetch) that reads base URL from env (NEXT_PUBLIC_API_URL)
- Auth: Keep X-API-Key for protected endpoints; later switch to token-based OAuth or JWT depending on product needs

3) Routing & layout
- Landing page: /
- Dashboard (authenticated): /dashboard
- Upload: integrated into dashboard (modal or dedicated page)

4) Component strategy
- Atomic components first (Button, Input, Card, Logo)
- Higher-level layouts (Header, Footer, Hero, UploadPanel)
- Use design tokens from DESIGN.md as Tailwind config variables or CSS variables

5) Testing and tooling
- Use Storybook for visual regression and component catalog
- Use Playwright for E2E checks once the UI is scaffolded

6) Next steps after design approval
- Create a minimal Next.js scaffold with layout and logo placement
- Implement atomics and a simple Upload flow connecting to backend API
