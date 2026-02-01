import React from 'react'
import Container from './Container'
import Heading from './Heading'

export default {
  title: 'UI/Container & Heading',
}

export const Default = () => (
  <Container>
    <Heading level={1}>ZEUSONIC</Heading>
    <p className="text-muted">Sample heading inside container</p>
  </Container>
)
