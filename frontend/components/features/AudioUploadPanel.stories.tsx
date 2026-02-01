import React from 'react'
import AudioUploadPanel from './AudioUploadPanel'

export default {
  title: 'Features/AudioUploadPanel',
  component: AudioUploadPanel,
  argTypes: {
    isDragging: { control: 'boolean' },
    hasFile: { control: 'boolean' },
    isUploading: { control: 'boolean' },
    disabled: { control: 'boolean' },
  },
}

const Template = (args: any) => <AudioUploadPanel {...args} />

export const Default = Template.bind({})
Default.args = {
  isDragging: false,
  hasFile: false,
  isUploading: false,
  disabled: false,
}

export const Dragging = Template.bind({})
Dragging.args = {
  isDragging: true,
}

export const FileSelected = Template.bind({})
FileSelected.args = {
  hasFile: true,
}

export const Uploading = Template.bind({})
Uploading.args = {
  isUploading: true,
}

export const Disabled = Template.bind({})
Disabled.args = {
  disabled: true,
}
