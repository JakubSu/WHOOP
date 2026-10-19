import { useCallback, useEffect, useState } from 'react'
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native'
import { StatusBar } from 'expo-status-bar'
import * as Linking from 'expo-linking'
import * as WebBrowser from 'expo-web-browser'
import { clearSession, getCurrentUser, restoreTokens } from './src/api'
import { AuthScreen } from './src/screens/AuthScreen'
import { TodayScreen } from './src/screens/TodayScreen'
import type { UserProfile } from './src/types'

WebBrowser.maybeCompleteAuthSession()

export default function App() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [booting, setBooting] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    let active = true
    async function bootstrap() {
      try {
        const hasSession = await restoreTokens()
        if (!hasSession) return
        const profile = await getCurrentUser()
        if (active) setUser(profile)
      } catch {
        await clearSession()
      } finally {
        if (active) setBooting(false)
      }
    }
    void bootstrap()
    return () => { active = false }
  }, [])

  const completeWhoopConnect = useCallback(async () => {
    try {
      const profile = await getCurrentUser()
      setUser(profile)
      setRefreshKey((key) => key + 1)
    } catch {
      setRefreshKey((key) => key + 1)
    }
  }, [])

  useEffect(() => {
    const subscription = Linking.addEventListener('url', ({ url }) => {
      if (url.startsWith('whoopmobile://connect-whoop/success')) void completeWhoopConnect()
    })
    void Linking.getInitialURL().then((url) => {
      if (url?.startsWith('whoopmobile://connect-whoop/success')) void completeWhoopConnect()
    })
    return () => subscription.remove()
  }, [completeWhoopConnect])

  if (booting) {
    return <View style={styles.boot}><StatusBar style="dark" /><ActivityIndicator size="large" color="#286244" /><Text style={styles.bootText}>Getting things ready…</Text></View>
  }

  return (
    <View style={styles.root}>
      <StatusBar style="dark" />
      {user ? (
        <TodayScreen
          key={user.id}
          user={user}
          refreshKey={refreshKey}
          onLogout={async () => { await clearSession(); setUser(null) }}
          onSessionExpired={() => { void clearSession().then(() => setUser(null)) }}
        />
      ) : <AuthScreen onSignedIn={setUser} />}
    </View>
  )
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#f3f5f1' },
  boot: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, backgroundColor: '#f3f5f1' },
  bootText: { color: '#667168', fontSize: 14 },
})
