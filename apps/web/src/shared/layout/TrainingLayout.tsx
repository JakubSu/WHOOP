import { type ReactNode } from 'react'
import { WhoopConnectionPrompt } from './WhoopConnectionPrompt'
import { WhoopMetricsHeader } from './WhoopMetricsHeader'

type TrainingLayoutProps = {
  children: ReactNode
}

export function TrainingLayout({ children }: TrainingLayoutProps) {
  return (
    <main className="min-h-screen bg-background p-0 sm:p-6">
      <section className="mx-auto grid min-h-screen w-full max-w-lg grid-rows-[auto_1fr] bg-card p-4 text-card-foreground shadow-xl sm:min-h-[calc(100vh-3rem)] sm:rounded-3xl sm:border">
        <WhoopMetricsHeader />
        {children}
      </section>
      <WhoopConnectionPrompt />
    </main>
  )
}
