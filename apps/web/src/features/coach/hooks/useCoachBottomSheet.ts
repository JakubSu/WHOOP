import { type PointerEvent, useCallback, useEffect, useRef, useState } from 'react'

const COLLAPSE_DRAG_DISTANCE = 96

export function useCoachBottomSheet(enabled: boolean) {
  const [isOpen, setIsOpen] = useState(false)
  const startY = useRef<number | null>(null)

  useEffect(() => {
    if (!enabled) setIsOpen(false)
  }, [enabled])

  const open = useCallback(() => setIsOpen(true), [])
  const close = useCallback(() => setIsOpen(false), [])

  const onDragStart = useCallback((event: PointerEvent<HTMLElement>) => {
    startY.current = event.clientY
    event.currentTarget.setPointerCapture(event.pointerId)
  }, [])

  const onDragEnd = useCallback((event: PointerEvent<HTMLElement>) => {
    if (startY.current !== null && event.clientY - startY.current >= COLLAPSE_DRAG_DISTANCE) {
      setIsOpen(false)
    }
    startY.current = null
  }, [])

  return { isOpen, open, close, onDragStart, onDragEnd }
}
