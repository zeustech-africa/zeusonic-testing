# AudioUploadPanel live integration

This file documents how the `AudioUploadPanel` is wired to the backend for real uploads.

Overview
- The `AudioUploadPanel` component supports a `live` prop. When `live` is true, it performs a JWT-scoped multipart upload (`POST /api/v1/projects/{project_id}/audio`) using `XMLHttpRequest` so it can track upload progress. The response returns a `track_id` for downstream workflows.

Local dev
- The component uses JWT (Authorization: Bearer) for project-scoped uploads.
- Run the backend: `uvicorn backend.main:app --reload`
- Authenticate via the standard login flow to obtain a JWT.

Storybook
- `Features/AudioUploadPanel/Live` is a Storybook story that demonstrates the same live wiring, but it replaces `window.XMLHttpRequest` and `window.fetch` with lightweight in-story mocks so no real network is used in Storybook.

Behavior & safety
- Upload progress is displayed as a percent while uploading.
- After the upload completes the component surfaces the new track id in status text (analysis runs in the background).
- Errors (missing JWT, network error, backend error) are surfaced via the component's status text.

Notes
- The Storybook interactive mock and its play tests remain unchanged and still provide the UI-only state machine.
- Pages `/generate` and `/dashboard` pass `live` to enable real upload integration during local development.
