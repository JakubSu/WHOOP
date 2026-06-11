import { type ReactNode } from 'react'
import { WhoopConnectionPrompt } from './WhoopConnectionPrompt'
import { WhoopMetricsHeader } from './WhoopMetricsHeader'

type TrainingLayoutProps = {
  children: ReactNode
}

export function TrainingLayout({ children }: TrainingLayoutProps) {
  return (
    <main className="training-shell">
      <section className="training-surface">
        <WhoopMetricsHeader />
        {children}
      </section>
      <WhoopConnectionPrompt />
    </main>
  )
}
