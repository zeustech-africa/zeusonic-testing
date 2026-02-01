import { useRef, useEffect } from 'react'

export default function useLongPress(onLongPress: () => void, ms = 600) {
  const timer = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (timer.current) window.clearTimeout(timer.current)
    }
  }, [])

  function onTouchStart() {
    // start timer
    timer.current = window.setTimeout(() => {
      onLongPress()
      timer.current = null
    }, ms)
  }

  function onTouchEnd() {
    if (timer.current) {
      window.clearTimeout(timer.current)
      timer.current = null
    }
  }

  return { onTouchStart, onTouchEnd }
}
