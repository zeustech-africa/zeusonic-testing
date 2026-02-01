import React from 'react'
import Divider from './Divider'

export default {
  title: 'UI/Divider',
  component: Divider,
}

export const Default = () => (
  <>
    <div className="text-muted">Above</div>
    <Divider />
    <div className="text-muted">Below</div>
  </>
)
