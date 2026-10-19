import { View, Text, StyleSheet } from 'react-native'
import Svg, { Circle } from 'react-native-svg'

const SIZE = 92
const STROKE = 7
const RADIUS = (SIZE - STROKE) / 2
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

export function MetricRing({
  label,
  value,
  progress,
  color,
}: {
  label: string
  value: string
  progress: number | null
  color: string
}) {
  const safeProgress = progress === null ? 0 : Math.max(0, Math.min(progress, 1))
  return (
    <View style={styles.wrap} accessibilityRole="image" accessibilityLabel={`${label}: ${value}`}>
      <View style={styles.graph}>
        <Svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
          <Circle cx={SIZE / 2} cy={SIZE / 2} r={RADIUS} fill="none" stroke="#e6e9e4" strokeWidth={STROKE} />
          {progress !== null ? (
            <Circle
              cx={SIZE / 2}
              cy={SIZE / 2}
              r={RADIUS}
              fill="none"
              stroke={color}
              strokeWidth={STROKE}
              strokeLinecap="round"
              strokeDasharray={`${CIRCUMFERENCE} ${CIRCUMFERENCE}`}
              strokeDashoffset={CIRCUMFERENCE * (1 - safeProgress)}
              rotation={-90}
              origin={`${SIZE / 2}, ${SIZE / 2}`}
            />
          ) : null}
        </Svg>
        <Text style={styles.value}>{value}</Text>
      </View>
      <Text style={styles.label}>{label}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: { alignItems: 'center', flex: 1 },
  graph: { width: SIZE, height: SIZE, alignItems: 'center', justifyContent: 'center' },
  value: { position: 'absolute', color: '#202a23', fontSize: 20, fontWeight: '700', fontVariant: ['tabular-nums'] },
  label: { marginTop: 9, color: '#667168', fontSize: 11, fontWeight: '700', letterSpacing: 0.5, textTransform: 'uppercase' },
})
