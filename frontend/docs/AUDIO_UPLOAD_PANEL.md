# AudioUploadPanel visual states

This document describes the visual state contract for the `AudioUploadPanel` component. It is intentionally UI-only: no file handling, network calls, or backend logic are implemented here.

## Purpose
Lock down the visual states the final upload UI will surface so frontend and design can align before integration with the backend and upload/job lifecycle.

## Props (visual-only)
- `isDragging?: boolean` — highlights the drop zone (accent border / subtle glow) to show a file is being dragged over the panel.
- `hasFile?: boolean` — shows a filename placeholder (`"track.wav selected"`) to simulate a selected file.
- `isUploading?: boolean` — disables the primary action and displays `"Uploading..."` to represent an in-progress upload.
- `disabled?: boolean` — lowers opacity and applies `cursor: not-allowed` to indicate the control is disabled.

## Important rules
- These props are purely presentational: they do not perform any file system or network work and do not create side effects.
- After the UI contract is accepted in Storybook, the next step will be to wire the component to real upload logic and lifecycle (upload start → progress → completed/failed → job polling).

## Interactive Storybook Mock
A Storybook-only interactive mock exists to validate the end-to-end UI flow without any backend or file handling.

Behavior:
- Uses React `useState` inside the story to simulate `hasFile`, `isUploading`, `disabled`, and `isDragging` transitions.
- Flow demonstrated:
  1. Initial — no file selected
  2. "Select file" (storybook control) → `hasFile = true`
  3. "Upload" (storybook control) → `isUploading = true`, `disabled = true`
  4. After a short timeout — `isUploading = false`, `disabled = false`, show "Upload complete" placeholder
- Notes:
  - Deterministic simulation only; no actual `<input type="file">`, no drag-drop handlers, and no network calls.
  - Purpose: allow designers and developers to validate interaction timing and messaging before wiring real upload logic.
