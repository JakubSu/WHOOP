export const COACH_SCROLL_BOTTOM_THRESHOLD = 48

export function isNearCoachScrollBottom({ scrollHeight, scrollTop, clientHeight }: { scrollHeight: number; scrollTop: number; clientHeight: number }) {
  return scrollHeight - scrollTop - clientHeight <= COACH_SCROLL_BOTTOM_THRESHOLD
}

export function scrollTopAfterPrepend({ previousHeight, previousTop, nextHeight }: { previousHeight: number; previousTop: number; nextHeight: number }) {
  return previousTop + nextHeight - previousHeight
}
