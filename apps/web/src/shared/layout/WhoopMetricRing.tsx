type WhoopMetricRingProps = {
  label: string
  value: number | null
  max: number
  color: string
  unit?: string
}

export function WhoopMetricRing({
  label,
  value,
  max,
  color,
  unit = '',
}: WhoopMetricRingProps) {
  const normalized = value === null ? 0 : Math.max(0, Math.min(value / max, 1))
  const degrees = Math.round(normalized * 360)
  const displayValue = value === null ? '--' : Math.round(value)

  return (
    <div className="metric-ring">
      <div
        className="metric-ring__dial"
        style={{
          background: `conic-gradient(${color} ${degrees}deg, #e7e9df 0deg)`,
        }}
      >
        <span>
          {displayValue}
          {value !== null ? unit : ''}
        </span>
      </div>
      <span className="metric-ring__label">{label}</span>
    </div>
  )
}
