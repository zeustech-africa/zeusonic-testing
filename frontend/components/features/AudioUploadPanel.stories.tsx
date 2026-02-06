import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import AudioUploadPanel from './AudioUploadPanel'

const meta = {
  title: 'Features/AudioUploadPanel',
  component: AudioUploadPanel,
  argTypes: {
    isDragging: { control: 'boolean' },
    hasFile: { control: 'boolean' },
    isUploading: { control: 'boolean' },
    disabled: { control: 'boolean' },
  },
} satisfies Meta<typeof AudioUploadPanel>

export default meta

type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    isDragging: false,
    hasFile: false,
    isUploading: false,
    disabled: false,
  },
}

export const Dragging: Story = {
  args: {
    isDragging: true,
  },
}

export const FileSelected: Story = {
  args: {
    hasFile: true,
  },
}

export const Uploading: Story = {
  args: {
    isUploading: true,
  },
}

export const Disabled: Story = {
  args: {
    disabled: true,
  },
}
