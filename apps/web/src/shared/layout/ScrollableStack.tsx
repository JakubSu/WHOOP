import { type ReactNode } from 'react'

type ScrollableStackProps = {
  children: ReactNode
  empty?: ReactNode
}

export function ScrollableStack({ children, empty }: ScrollableStackProps) {
  return <div className="scrollable-stack">{children || empty}</div>
}
