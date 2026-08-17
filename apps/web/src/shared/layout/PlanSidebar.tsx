import { WeekPlanList } from '../../features/training/components/WeekPlanList'

export function PlanSidebar({ showWeekNavigator }: { showWeekNavigator: boolean }) {
  if (!showWeekNavigator) return null

  return (
    <div className="grid min-h-0 flex-1 grid-rows-[auto_1fr] border-t border-border pt-4">
      <p className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-primary">Week</p>
      <WeekPlanList compact />
    </div>
  )
}
