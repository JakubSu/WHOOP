import { type ReactNode } from 'react'

type ScrollableStackProps = {
  children: ReactNode
  empty?: ReactNode
}

export function ScrollableStack({ children, empty }: ScrollableStackProps) {
  return <div className="grid min-h-0 content-start gap-3 overflow-y-auto py-1">{children || empty}</div>
}
