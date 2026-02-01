import React, { useState } from 'react'
import AudioUploadPanel from './AudioUploadPanel'
import Button from '../ui/Button'

export default {
  title: 'Features/AudioUploadPanel/Interactive',
  component: AudioUploadPanel,
}

export const InteractiveMock = () => {
  const [hasFile, setHasFile] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [disabled, setDisabled] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [complete, setComplete] = useState(false)
  const [simulateError, setSimulateError] = useState(false)

  const selectFile = () => {
    setHasFile(true)
    setComplete(false)
    setSimulateError(false)
  }

  const upload = () => {
    if (!hasFile) return
    setIsUploading(true)
    setDisabled(true)
    setComplete(false)

    setTimeout(() => {
      setIsUploading(false)
      setDisabled(false)
      if (simulateError) {
        // remain in error visual state
      } else {
        setComplete(true)
        setHasFile(false)
      }
    }, 1500)
  }

  const reset = () => {
    setHasFile(false)
    setIsUploading(false)
    setDisabled(false)
    setComplete(false)
    setSimulateError(false)
    setIsDragging(false)
  }

  return (
    <div className="space-y-4">
      <AudioUploadPanel isDragging={isDragging} hasFile={hasFile} isUploading={isUploading} disabled={disabled} />

      <div className="flex gap-2">
        <Button variant="ghost" size="sm" onClick={() => setIsDragging((s) => !s)}>
          {isDragging ? 'Stop Drag' : 'Simulate Drag'}
        </Button>

        <Button variant="ghost" size="sm" onClick={selectFile}>
          Select file
        </Button>

        <Button variant="primary" size="sm" onClick={upload} disabled={!hasFile || isUploading}>
          Upload
        </Button>

        <Button variant="ghost" size="sm" onClick={() => setSimulateError((e) => !e)}>
          {simulateError ? 'Simulate Success' : 'Simulate Error'}
        </Button>

        <Button variant="ghost" size="sm" onClick={reset}>
          Reset
        </Button>
      </div>

      <div>
        {isUploading && <div className="text-muted text-sm">Uploading…</div>}
        {complete && <div className="text-accent text-sm font-medium">Upload complete (simulated)</div>}
        {simulateError && !isUploading && <div className="text-red-400 text-sm font-medium">Upload failed (simulated)</div>}
      </div>
    </div>
  )
}

// Storybook play interaction tests (UI-only)
InteractiveMock.play = async ({ canvasElement }) => {
  const { within, userEvent, waitFor } = await import('@storybook/testing-library')
  const { expect } = await import('@storybook/jest')
  const canvas = within(canvasElement)

  // 1) Select file
  const selectBtn = await canvas.getByRole('button', { name: /Select file/i })
  await userEvent.click(selectBtn)

  // Expect filename placeholder to appear
  await waitFor(() => expect(canvas.getByText(/track\.wav selected/i)).toBeInTheDocument())

  // 2) Click Upload and assert uploading state
  const uploadBtn = await canvas.getByRole('button', { name: /Upload/i })
  await userEvent.click(uploadBtn)

  // Uploading label and disabled state on button
  await waitFor(() => expect(uploadBtn).toHaveTextContent(/Uploading/i))
  await waitFor(() => expect(uploadBtn).toBeDisabled())

  // The panel wrapper should show disabled styles (opacity-50) during upload
  const heading = await canvas.getByRole('heading', { name: /Upload audio/i })
  expect(heading.parentElement).toHaveClass('opacity-50')

  // Uploading status text appears
  await waitFor(() => expect(canvas.getByText(/Uploading…/i)).toBeInTheDocument())

  // 3) After timeout, success message appears
  await waitFor(() => expect(canvas.getByText(/Upload complete \(simulated\)/i)).toBeInTheDocument(), { timeout: 2000 })

  // 4) Now test error flow: select file, toggle simulate error, upload
  const selectBtn2 = await canvas.getByRole('button', { name: /Select file/i })
  await userEvent.click(selectBtn2)

  const simulateErrorBtn = await canvas.getByRole('button', { name: /Simulate Error/i })
  await userEvent.click(simulateErrorBtn)

  const uploadBtn2 = await canvas.getByRole('button', { name: /Upload/i })
  await userEvent.click(uploadBtn2)

  // Wait for error state
  await waitFor(() => expect(canvas.getByText(/Upload failed \(simulated\)/i)).toBeInTheDocument(), { timeout: 2000 })

  // 5) Reset returns to initial
  const resetBtn = await canvas.getByRole('button', { name: /Reset/i })
  await userEvent.click(resetBtn)
  await waitFor(() => expect(canvas.queryByText(/track\.wav selected/i)).toBeNull())
}
