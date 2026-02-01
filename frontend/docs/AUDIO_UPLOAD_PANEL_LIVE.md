# AudioUploadPanel live integration

This file documents how the `AudioUploadPanel` is wired to the backend for real uploads and job polling.

Overview
- The `AudioUploadPanel` component supports a `live` prop. When `live` is true, it performs a multipart upload (`POST /api/v1/audio/upload`) using `XMLHttpRequest` so it can track upload progress, and then polls `GET /api/v1/audio/jobs/{job_id}` every 2s to update the job status.

Local dev & API key
- The component reads a dev API key from `localStorage.ZEUSONIC_API_KEY` if present and sends it as `X-API-Key` header during upload.
- To set the demo key locally:
  1. Run the backend: `uvicorn backend.main:app --reload`
  2. Copy the demo key printed during startup or from `backend/.demo_api_key`
  3. In the browser console: `localStorage.setItem('ZEUSONIC_API_KEY', '<your-key>')`

Storybook
- `Features/AudioUploadPanel/Live` is a Storybook story that demonstrates the same live wiring, but it replaces `window.XMLHttpRequest` and `window.fetch` with lightweight in-story mocks so no real network is used in Storybook.

Behavior & safety
- Upload progress is displayed as a percent while uploading.
- After the upload completes the component polls the job endpoint until the job reaches `completed` or `failed`.
- Errors (missing API key, network error, backend error) are surfaced via the component's status text.

Notes
- The Storybook interactive mock and its play tests remain unchanged and still provide the UI-only state machine.
- Pages `/generate` and `/dashboard` pass `live` to enable real upload integration during local development.
