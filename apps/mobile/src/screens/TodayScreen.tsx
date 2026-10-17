import { useCallback, useEffect, useState } from 'react'
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import * as WebBrowser from 'expo-web-browser'
import { ApiError, getWhoopAccessRequest, getWhoopConnectUrl, getWhoopSummary, getWorkout, getWorkoutExercises, getWorkoutLanding, requestWhoopAccess, whoopOauthReturnUrl } from '../api'
import { MetricRing } from '../components/MetricRing'
import { formatPrescription, formatRefreshedAt, formatToday, localDateIso } from '../formatters'
import type { UserProfile, WhoopAccessRequest, WhoopSummary, Workout, WorkoutExercise } from '../types'

type WorkoutState = { workout: Workout; exercises: WorkoutExercise[] } | null

export function TodayScreen({
  user,
  onLogout,
  onSessionExpired,
  refreshKey,
}: {
  user: UserProfile
  onLogout: () => void
  onSessionExpired: () => void
  refreshKey: number
}) {
  const [summary, setSummary] = useState<WhoopSummary | null>(null)
  const [workout, setWorkout] = useState<WorkoutState>(null)
  const [accessRequest, setAccessRequest] = useState<WhoopAccessRequest | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connectBusy, setConnectBusy] = useState(false)
  const [accessBusy, setAccessBusy] = useState(false)

  const load = useCallback(async () => {
    setError(null)
    try {
      const summaryResult = await getWhoopSummary().catch((requestError: unknown) => {
        if (requestError instanceof ApiError && requestError.status === 404) {
          return { connected: false } satisfies WhoopSummary
        }
        throw requestError
      })
      setSummary(summaryResult)

      const landing = await getWorkoutLanding(localDateIso())
      if (landing.has_workout_today && landing.selected_workout?.is_today) {
        const id = landing.selected_workout.id
        const [details, exercises] = await Promise.all([getWorkout(id), getWorkoutExercises(id)])
        setWorkout({ workout: details, exercises: [...exercises].sort((a, b) => a.sort_order - b.sort_order) })
      } else {
        setWorkout(null)
      }

      if (!user.whoop_connection_allowed) {
        const access = await getWhoopAccessRequest().catch((requestError: unknown) => {
          if (requestError instanceof ApiError && requestError.status === 404) return { status: 'none' as const }
          throw requestError
        })
        setAccessRequest(access)
      }
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 401) {
        onSessionExpired()
      } else {
        setError(requestError instanceof Error ? requestError.message : 'Could not load today’s training.')
      }
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [onSessionExpired, user.whoop_connection_allowed])

  useEffect(() => { void load() }, [load, refreshKey])

  async function connectWhoop() {
    setConnectBusy(true)
    setError(null)
    try {
      const { connect_url } = await getWhoopConnectUrl()
      const result = await WebBrowser.openAuthSessionAsync(connect_url, whoopOauthReturnUrl)
      if (result.type === 'success' && result.url.startsWith(whoopOauthReturnUrl.split('?')[0])) {
        await load()
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not start WHOOP connection.')
    } finally {
      setConnectBusy(false)
    }
  }

  async function askForWhoopAccess() {
    setAccessBusy(true)
    setError(null)
    try {
      setAccessRequest(await requestWhoopAccess())
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not request WHOOP access.')
    } finally {
      setAccessBusy(false)
    }
  }

  const recovery = summary?.recovery_score ?? null
  const sleep = summary?.sleep_performance_percent ?? null
  const strain = summary?.day_strain ?? null
  const accessStatus = user.whoop_connection_allowed ? 'approved' : accessRequest?.status ?? 'none'

  return (
    <View style={styles.screen}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); void load() }} tintColor="#286244" />}
      >
        <View style={styles.topBar}>
          <View style={styles.brandRow}><View style={styles.smallMark}><Text style={styles.smallMarkText}>W</Text></View><Text style={styles.brandName}>WHOOP</Text></View>
          <Pressable accessibilityRole="button" onPress={onLogout} hitSlop={10}><Text style={styles.logout}>Sign out</Text></Pressable>
        </View>

        <Text style={styles.greeting}>Today</Text>
        <Text style={styles.date}>{formatToday()}</Text>

        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <View><Text style={styles.sectionTitle}>Your day</Text><Text style={styles.sectionSubtitle}>WHOOP summary</Text></View>
            {summary?.connected && summary.refreshed_at ? <Text style={styles.updated}>{formatRefreshedAt(summary.refreshed_at)}</Text> : null}
          </View>
          {loading && !summary ? (
            <View style={styles.metricLoading}><ActivityIndicator color="#286244" /><Text style={styles.loadingText}>Loading WHOOP data…</Text></View>
          ) : (
            <View style={styles.rings}>
              <MetricRing label="Recovery" value={recovery === null ? '—' : `${Math.round(recovery)}%`} progress={recovery === null ? null : recovery / 100} color="#39a878" />
              <MetricRing label="Sleep" value={sleep === null ? '—' : `${Math.round(sleep)}%`} progress={sleep === null ? null : sleep / 100} color="#5c91d6" />
              <MetricRing label="Strain" value={strain === null ? '—' : strain.toFixed(1)} progress={strain === null ? null : strain / 21} color="#e1a242" />
            </View>
          )}
          {!summary?.connected ? (
            <View style={styles.connectBox}>
              <Text style={styles.connectTitle}>{accessStatus === 'pending' ? 'WHOOP access requested' : accessStatus === 'rejected' ? 'WHOOP access needs approval' : 'Connect your WHOOP'}</Text>
              <Text style={styles.connectCopy}>{accessStatus === 'pending' ? 'Your request is waiting for approval.' : accessStatus === 'approved' ? 'Link your account to see recovery, sleep, and strain here.' : 'Link your account to see recovery, sleep, and strain here.'}</Text>
              {accessStatus === 'approved' ? (
                <ActionButton title={connectBusy ? 'Opening WHOOP…' : 'Connect WHOOP'} disabled={connectBusy} onPress={connectWhoop} />
              ) : accessStatus !== 'pending' ? (
                <ActionButton title={accessBusy ? 'Requesting…' : accessStatus === 'rejected' ? 'Request access again' : 'Request WHOOP access'} disabled={accessBusy} onPress={askForWhoopAccess} />
              ) : null}
            </View>
          ) : null}
          {summary?.connected && recovery === null && sleep === null && strain === null ? <Text style={styles.noMetrics}>No scored WHOOP data is available yet.</Text> : null}
        </View>

        <View style={styles.workoutHeading}>
          <View><Text style={styles.eyebrow}>YOUR PLAN</Text><Text style={styles.sectionTitleLarge}>Today’s workout</Text></View>
          {workout?.workout.expected_time ? <View style={styles.duration}><Text style={styles.durationText}>{workout.workout.expected_time} min</Text></View> : null}
        </View>

        {loading && !workout ? (
          <View style={[styles.card, styles.workoutLoading]}><ActivityIndicator color="#286244" /><Text style={styles.loadingText}>Finding today’s workout…</Text></View>
        ) : workout ? (
          <View style={styles.card}>
            <Text style={styles.workoutName}>{workout.workout.name}</Text>
            <Text style={styles.exerciseCount}>{workout.exercises.length} {workout.exercises.length === 1 ? 'exercise' : 'exercises'}</Text>
            {workout.exercises.length ? (
              <View style={styles.exerciseList}>
                {workout.exercises.map((exercise, index) => {
                  const formatted = formatPrescription(exercise)
                  return (
                    <View key={exercise.id} style={[styles.exerciseRow, index > 0 && styles.exerciseBorder]}>
                      <View style={styles.exerciseIndex}><Text style={styles.exerciseIndexText}>{String(index + 1).padStart(2, '0')}</Text></View>
                      <View style={styles.exerciseBody}><Text style={styles.exerciseName}>{formatted.name}</Text><Text style={styles.prescription}>{formatted.prescription}</Text></View>
                    </View>
                  )
                })}
              </View>
            ) : <Text style={styles.noExercises}>This workout has no exercises yet.</Text>}
          </View>
        ) : (
          <View style={[styles.card, styles.emptyWorkout]}>
            <View style={styles.emptyIcon}><Text style={styles.emptyIconText}>↗</Text></View>
            <Text style={styles.emptyTitle}>Nothing planned for today</Text>
            <Text style={styles.emptyCopy}>Your next training day will show up here when it’s on your plan.</Text>
          </View>
        )}
        {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
      </ScrollView>
    </View>
  )
}

function ActionButton({ title, disabled, onPress }: { title: string; disabled: boolean; onPress: () => void }) {
  return <Pressable accessibilityRole="button" disabled={disabled} onPress={onPress} style={({ pressed }) => [styles.actionButton, pressed && styles.pressed, disabled && styles.buttonDisabled]}><Text style={styles.actionButtonText}>{title}</Text></Pressable>
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: '#f3f5f1' },
  content: { paddingHorizontal: 20, paddingTop: 14, paddingBottom: 40 },
  topBar: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: 9 },
  smallMark: { width: 29, height: 29, borderRadius: 10, backgroundColor: '#286244', alignItems: 'center', justifyContent: 'center' },
  smallMarkText: { color: '#fff', fontSize: 15, fontWeight: '800' },
  brandName: { color: '#202a23', fontSize: 13, fontWeight: '900', letterSpacing: 1.6 },
  logout: { color: '#667168', fontSize: 13, fontWeight: '600', padding: 5 },
  greeting: { marginTop: 18, color: '#202a23', fontSize: 31, fontWeight: '800', letterSpacing: -0.7 },
  date: { marginTop: 2, marginBottom: 20, color: '#667168', fontSize: 14 },
  card: { padding: 17, borderRadius: 20, borderWidth: 1, borderColor: '#e0e5df', backgroundColor: '#fff' },
  cardHeader: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between' },
  sectionTitle: { color: '#202a23', fontSize: 17, fontWeight: '800' },
  sectionSubtitle: { marginTop: 3, color: '#89928b', fontSize: 12 },
  updated: { marginTop: 3, color: '#89928b', fontSize: 11 },
  rings: { flexDirection: 'row', justifyContent: 'space-around', marginTop: 22, marginBottom: 20 },
  metricLoading: { minHeight: 128, alignItems: 'center', justifyContent: 'center', gap: 9 },
  loadingText: { color: '#7a857c', fontSize: 13 },
  connectBox: { marginTop: 2, padding: 14, borderRadius: 14, backgroundColor: '#f3f6f2' },
  connectTitle: { color: '#26372c', fontSize: 14, fontWeight: '700' },
  connectCopy: { marginTop: 5, color: '#69766c', fontSize: 12, lineHeight: 18 },
  actionButton: { minHeight: 42, marginTop: 12, paddingHorizontal: 14, borderRadius: 11, backgroundColor: '#286244', alignItems: 'center', justifyContent: 'center', alignSelf: 'flex-start' },
  actionButtonText: { color: '#fff', fontSize: 13, fontWeight: '700' },
  pressed: { opacity: 0.83 },
  buttonDisabled: { opacity: 0.64 },
  noMetrics: { marginTop: 4, color: '#89928b', fontSize: 12, textAlign: 'center' },
  workoutHeading: { marginTop: 26, marginBottom: 12, flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between' },
  eyebrow: { color: '#46765a', fontSize: 10, fontWeight: '800', letterSpacing: 1.5 },
  sectionTitleLarge: { marginTop: 3, color: '#202a23', fontSize: 22, fontWeight: '800', letterSpacing: -0.35 },
  duration: { marginBottom: 2, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 20, backgroundColor: '#e6efe7' },
  durationText: { color: '#286244', fontSize: 11, fontWeight: '700' },
  workoutName: { color: '#202a23', fontSize: 20, fontWeight: '800', letterSpacing: -0.3 },
  exerciseCount: { marginTop: 4, color: '#89928b', fontSize: 12 },
  exerciseList: { marginTop: 13 },
  exerciseRow: { minHeight: 62, flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 11 },
  exerciseBorder: { borderTopWidth: 1, borderColor: '#edf0ed' },
  exerciseIndex: { width: 30, height: 30, borderRadius: 10, backgroundColor: '#f1f4f0', alignItems: 'center', justifyContent: 'center' },
  exerciseIndexText: { color: '#718076', fontSize: 10, fontWeight: '800' },
  exerciseBody: { flex: 1 },
  exerciseName: { color: '#26322a', fontSize: 14, fontWeight: '700' },
  prescription: { marginTop: 3, color: '#7b867e', fontSize: 12 },
  noExercises: { marginTop: 16, color: '#7b867e', fontSize: 13 },
  workoutLoading: { minHeight: 110, alignItems: 'center', justifyContent: 'center', gap: 10 },
  emptyWorkout: { minHeight: 165, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 24 },
  emptyIcon: { width: 38, height: 38, borderRadius: 13, backgroundColor: '#eaf1ea', alignItems: 'center', justifyContent: 'center' },
  emptyIconText: { color: '#46765a', fontSize: 22, fontWeight: '700' },
  emptyTitle: { marginTop: 11, color: '#26322a', fontSize: 15, fontWeight: '700' },
  emptyCopy: { marginTop: 5, color: '#7b867e', fontSize: 12, lineHeight: 18, textAlign: 'center' },
  error: { marginTop: 12, color: '#a23b32', fontSize: 13, lineHeight: 19 },
})
