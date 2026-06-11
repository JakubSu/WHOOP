import { useWhoopSummary } from '../../features/whoop/hooks/useWhoopSummary'
import { UserProfileButton } from './UserProfileButton'
import { WhoopMetricRing } from './WhoopMetricRing'

function recoveryColor(value: number | null) {
  if (value === null) {
    return '#A0A7A0'
  }
  if (value >= 67) {
    return '#00F19F'
  }
  if (value >= 34) {
    return '#FFCC00'
  }
  return '#FF3B30'
}

export function WhoopMetricsHeader() {
  const summary = useWhoopSummary()
  const data = summary.data

  return (
    <header className="training-header">
      <div className="metrics-group" aria-label="WHOOP metrics">
        <WhoopMetricRing
          label="Sleep"
          value={data?.sleep_performance_percent ?? null}
          max={100}
          color="#7BA1BB"
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
          color="#0093E7"
        />
        <span className="powered-by">Powered by WHOOP</span>
      </div>
      <UserProfileButton />
    </header>
  )
}
