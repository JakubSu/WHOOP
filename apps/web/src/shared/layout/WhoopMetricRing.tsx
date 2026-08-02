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
    <div className="grid justify-items-center gap-1">
      <div
        className="grid size-11 place-items-center rounded-full p-1"
        style={{
          background: `conic-gradient(${color} ${degrees}deg, var(--muted-foreground) 0deg)`,
        }}
      >
        <span className="grid size-8 place-items-center rounded-full bg-card text-xs font-black">
          {displayValue}
          {value !== null ? unit : ''}
        </span>
      </div>
      <span className="text-[.65rem] font-bold text-muted-foreground">{label}</span>
    </div>
  )
}
