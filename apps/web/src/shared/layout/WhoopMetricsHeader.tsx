import { useWhoopSummary } from '../../features/whoop/hooks/useWhoopSummary'
import { UserProfileButton } from './UserProfileButton'
import { WhoopMetricRing } from './WhoopMetricRing'

function recoveryColor(value: number | null) {
  if (value === null) {
    return 'var(--muted-foreground)'
  }
  if (value >= 67) {
    return 'var(--whoop-recovery-good)'
  }
  if (value >= 34) {
    return 'var(--whoop-recovery-fair)'
  }
  return 'var(--whoop-recovery-low)'
}

export function WhoopMetricsHeader() {
  const summary = useWhoopSummary()
  const data = summary.data

  return (
    <header className="mb-2 grid grid-cols-[1fr_auto] items-start gap-3 lg:mb-5">
      <div className="grid grid-cols-3 gap-2" aria-label="WHOOP metrics">
        <WhoopMetricRing
          label="Sleep"
          value={data?.sleep_performance_percent ?? null}
          max={100}
          color="var(--whoop-sleep)"
          unit="%"
        />
        <WhoopMetricRing
          label="Recovery"
          value={data?.recovery_score ?? null}
          max={100}
          color={recoveryColor(data?.recovery_score ?? null)}
          unit="%"
        />
        <WhoopMetricRing
          label="Strain"
          value={data?.day_strain ?? null}
          max={21}
          color="var(--whoop-strain)"
        />
        <span className="col-span-3 text-[.65rem] font-bold uppercase text-muted-foreground">Powered by WHOOP</span>
      </div>
      <UserProfileButton />
    </header>
  )
}
