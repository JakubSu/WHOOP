import { useCallback, useLayoutEffect, useRef, useState } from 'react'
import { isNearCoachScrollBottom, scrollTopAfterPrepend } from '../services/coachScrollState'

export function useCoachAutoScroll({
  isOpen,
  messageCount,
  isStreaming,
  streamVersion,
}: {
  isOpen: boolean
  messageCount: number
  isStreaming: boolean
  streamVersion: number
}) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [isFollowing, setIsFollowing] = useState(true)
  const prependPosition = useRef<{ height: number; top: number } | null>(null)

  const scrollToLatest = useCallback((behavior: ScrollBehavior = 'smooth') => {
    const element = scrollRef.current
    if (!element) return
    element.scrollTo({ top: element.scrollHeight, behavior })
    setIsFollowing(true)
  }, [])

  const startFollowing = useCallback(() => {
    setIsFollowing(true)
    requestAnimationFrame(() => scrollToLatest('smooth'))
  }, [scrollToLatest])

  const prepareForPrepend = useCallback(() => {
    const element = scrollRef.current
    if (element) prependPosition.current = { height: element.scrollHeight, top: element.scrollTop }
  }, [])

  const onScroll = useCallback(() => {
    const element = scrollRef.current
    if (!element) return
    setIsFollowing(isNearCoachScrollBottom(element))
  }, [])

  useLayoutEffect(() => {
    const element = scrollRef.current
    const position = prependPosition.current
    if (!element || !position) return
    element.scrollTop = scrollTopAfterPrepend({ previousHeight: position.height, previousTop: position.top, nextHeight: element.scrollHeight })
    prependPosition.current = null
  }, [messageCount])

  useLayoutEffect(() => {
    if (!isOpen || !isFollowing) return
    const frame = requestAnimationFrame(() => scrollToLatest(isStreaming ? 'auto' : 'smooth'))
    return () => cancelAnimationFrame(frame)
  }, [isFollowing, isOpen, isStreaming, messageCount, scrollToLatest, streamVersion])

  return { scrollRef, isFollowing, onScroll, scrollToLatest, startFollowing, prepareForPrepend }
}
