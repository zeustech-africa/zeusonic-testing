import React from 'react'
import Input from './Input'

export default {
  title: 'UI/Input',
  component: Input,
}

export const Default = () => <Input placeholder="Type..." />
export const Error = () => <Input placeholder="Error" error />
export const Disabled = () => <Input placeholder="Disabled" disabled />
