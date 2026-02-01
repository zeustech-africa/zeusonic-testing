import React from 'react'
import Card from './Card'

export default {
  title: 'UI/Card',
  component: Card,
}

export const Default = () => (
  <Card>
    <div className="text-white">Card content</div>
  </Card>
)
