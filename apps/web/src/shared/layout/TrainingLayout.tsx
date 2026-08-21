import { type ReactNode } from 'react'
import { cn } from '../utils/cn'
import { CoachOverlay } from '../../features/coach/components/CoachOverlay'
import { CoachPanelProvider, useCoachPanel } from '../../features/coach/context/CoachPanelContext'
import { WhoopConnectionPrompt } from './WhoopConnectionPrompt'
import { WhoopMetricsHeader } from './WhoopMetricsHeader'
import { PlanSidebar } from './PlanSidebar'
import { useAuthStore } from '../../features/auth/store/authStore'

type TrainingLayoutProps = {
  children: ReactNode
  showWeekNavigator?: boolean
}

export function TrainingLayout({ children, showWeekNavigator = true }: TrainingLayoutProps) {
  return (
    <CoachPanelProvider>
      <TrainingWorkspace showWeekNavigator={showWeekNavigator}>{children}</TrainingWorkspace>
    </CoachPanelProvider>
  )
}

function TrainingWorkspace({ children, showWeekNavigator }: Required<TrainingLayoutProps>) {
  const coach = useCoachPanel()
  const user = useAuthStore((state) => state.user)
  const coachColumn = coach.mode === 'collapsed' ? 'lg:grid-cols-[19rem_minmax(0,1fr)_3rem]' : 'lg:grid-cols-[19rem_minmax(0,1fr)_24rem]'

  return (
    <main className="min-h-screen bg-background p-0 lg:h-screen lg:p-6">
      <div className={cn('mx-auto grid min-h-screen w-full max-w-2xl bg-card text-card-foreground shadow-xl lg:h-[calc(100dvh-3rem)] lg:min-h-0 lg:max-w-[1600px] lg:overflow-hidden lg:rounded-3xl lg:border', coachColumn)}>
        {user?.account_type === 'demo' ? (
          <div className="col-span-full flex items-center justify-center bg-primary px-3 py-1 text-center text-xs font-medium leading-4 text-primary-foreground lg:px-4 lg:py-1 lg:text-sm lg:leading-5">
            You’re exploring a one-hour demo with fictional data. Create an account to save your progress.
          </div>
        ) : null}
        <aside className="hidden min-h-0 flex-col overflow-y-auto border-r border-border bg-card p-5 lg:flex">
          <div data-tour="whoop-metrics-desktop"><WhoopMetricsHeader /></div>
          <PlanSidebar showWeekNavigator={showWeekNavigator} />
        </aside>
        <section className="grid min-h-0 grid-rows-[auto_1fr] overflow-hidden p-4 sm:p-6 lg:overflow-y-auto lg:p-0">
          <div className="lg:hidden" data-tour="whoop-metrics-mobile"><WhoopMetricsHeader /></div>
          {children}
        </section>
        <CoachOverlay />
      </div>
      <WhoopConnectionPrompt />
    </main>
  )
}
