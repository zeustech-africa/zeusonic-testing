import React from 'react'
import Badge from './Badge'

export default {
  title: 'UI/Badge',
  component: Badge,
}

export const Accent = () => <Badge variant="accent">Beta</Badge>
export const Muted = () => <Badge variant="muted">New</Badge>
