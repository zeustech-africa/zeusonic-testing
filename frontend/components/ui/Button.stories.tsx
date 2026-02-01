import React from 'react'
import Button from './Button'

export default {
  title: 'UI/Button',
  component: Button,
}

export const Primary = (args: any) => <Button {...args}>Primary</Button>
Primary.args = { variant: 'primary', size: 'md' }

export const PrimaryLarge = () => <Button variant="primary" size="lg">Large</Button>
export const Ghost = () => <Button variant="ghost">Ghost</Button>
export const Disabled = () => <Button disabled>Disabled</Button>
