import React from 'react'
import AudioUploadPanel from './AudioUploadPanel'
import type { Meta } from '@storybook/react'

export default {
  title: 'Features/AudioUploadPanel/Live',
  component: AudioUploadPanel,
} as Meta

// This story demonstrates the real upload + job polling behavior, but in Storybook
// we replace XHR and fetch with light mocks so no real network calls are made.
export const LiveMock = () => {
  return <AudioUploadPanel live />
}

// Play test: mock XHR and fetch, then simulate user selecting a file and uploading
LiveMock.play = async ({ canvasElement }) => {
  const { within, userEvent, waitFor } = await import('@storybook/testing-library')
  const { expect } = await import('@storybook/jest')
  const canvas = within(canvasElement)

  // Lightweight XHR mock
  class FakeXHR {
    public upload: any = {}
    public onload: any = null
    public onerror: any = null
    private _listeners: any = {}
    private _status: number = 201
    open(method: string, url: string) {}
    setRequestHeader(name: string, value: string) {}
    send(fd: FormData) {
      // simulate progress
      let loaded = 0
      const total = 100
      const interval = setInterval(() => {
        loaded += 25
        if (this.upload && this.upload.onprogress) {
          this.upload.onprogress({ lengthComputable: true, loaded, total })
        }
        if (loaded >= total) {
          clearInterval(interval)
          // final response: job_id
          const resp = JSON.stringify({ job_id: 'test-job-123' })
          if (this.onload) {
            (this as any).status = 201
            ;(this as any).responseText = resp
            this.onload()
          }
        }
      }, 150)
    }
  }

  // Inject fake XHR
  // @ts-ignore
  const OriginalXHR = window.XMLHttpRequest
  // @ts-ignore
  window.XMLHttpRequest = FakeXHR

  // Mock fetch for job polling: first queued, then processing, then completed
  let callCount = 0
  // @ts-ignore
  const originalFetch = window.fetch
  // @ts-ignore
  window.fetch = async (url: string) => {
    callCount += 1
    let status = 'queued'
    if (callCount >= 2) status = 'processing'
    if (callCount >= 4) status = 'completed'
    return {
      ok: true,
      json: async () => ({ job_id: 'test-job-123', filename: 'test.wav', status }),
    }
  }

  try {
    // Create a fake file and set it on the file input
    const input = canvas.getByRole('textbox', { hidden: true }) || canvas.getByLabelText(/file/i, { selector: 'input', hidden: true })
    // If no input accessible via role, find the hidden input directly
    let fileInput = input as HTMLInputElement
    if (!fileInput || fileInput.tagName !== 'INPUT') {
      fileInput = canvasElement.querySelector('input[type=file]') as HTMLInputElement
    }

    const file = new File(['dummy content'], 'test.wav', { type: 'audio/wav' })
    // programmatically set files
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false,
    })

    await waitFor(() => fileInput.dispatchEvent(new Event('change', { bubbles: true })))

    const selectBtn = canvas.getByRole('button', { name: /Select file/i })
    await userEvent.click(selectBtn)

    // Confirm filename appears
    await waitFor(() => expect(canvas.getByText(/test.wav/i)).toBeInTheDocument())

    const uploadBtn = canvas.getByRole('button', { name: /Upload/i })
    await userEvent.click(uploadBtn)

    // While uploading, progress and uploading text should appear
    await waitFor(() => expect(canvas.getByText(/Uploading/i)).toBeInTheDocument())

    // Wait for polling to reach completed state
    await waitFor(() => expect(canvas.getByText(/Processing complete/i)).toBeInTheDocument(), { timeout: 5000 })
  } finally {
    // restore originals
    // @ts-ignore
    window.XMLHttpRequest = OriginalXHR
    // @ts-ignore
    window.fetch = originalFetch
  }
}
