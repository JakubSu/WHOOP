import { useState } from 'react'
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'
import { ApiError, login, register } from '../api'
import type { UserProfile } from '../types'

export function AuthScreen({ onSignedIn }: { onSignedIn: (user: UserProfile) => void }) {
  const [isRegister, setIsRegister] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit() {
    setError(null)
    if (!email.trim() || !password || (isRegister && !name.trim())) {
      setError(isRegister ? 'Enter your name, email, and password.' : 'Enter your email and password.')
      return
    }
    setBusy(true)
    try {
      const user = isRegister
        ? await register(email.trim(), password, name.trim())
        : await login(email.trim(), password)
      onSignedIn(user)
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : 'Could not reach the WHOOP service.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <KeyboardAvoidingView style={styles.root} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.brandMark}><Text style={styles.brandMarkText}>W</Text></View>
        <Text style={styles.eyebrow}>YOUR TRAINING, IN CONTEXT</Text>
        <Text style={styles.title}>{isRegister ? 'Create your account' : 'Welcome back'}</Text>
        <Text style={styles.description}>Connect your WHOOP data and keep today’s training close.</Text>
        <View style={styles.form}>
          {isRegister ? (
            <TextInput
              accessibilityLabel="Name"
              autoCapitalize="words"
              autoComplete="name"
              onChangeText={setName}
              placeholder="Name"
              placeholderTextColor="#89928b"
              style={styles.input}
              value={name}
            />
          ) : null}
          <TextInput
            accessibilityLabel="Email"
            autoCapitalize="none"
            autoComplete="email"
            keyboardType="email-address"
            onChangeText={setEmail}
            placeholder="Email"
            placeholderTextColor="#89928b"
            style={styles.input}
            value={email}
          />
          <TextInput
            accessibilityLabel="Password"
            autoCapitalize="none"
            autoComplete={isRegister ? 'new-password' : 'password'}
            onChangeText={setPassword}
            placeholder="Password"
            placeholderTextColor="#89928b"
            secureTextEntry
            style={styles.input}
            value={password}
          />
          {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
          <Pressable accessibilityRole="button" disabled={busy} onPress={submit} style={({ pressed }) => [styles.primaryButton, pressed && styles.pressed, busy && styles.disabled]}>
            {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryButtonText}>{isRegister ? 'Create account' : 'Sign in'}</Text>}
          </Pressable>
          <Pressable accessibilityRole="button" disabled={busy} onPress={() => { setIsRegister((current) => !current); setError(null) }} style={styles.switchButton}>
            <Text style={styles.switchText}>{isRegister ? 'Already have an account? Sign in' : 'New here? Create an account'}</Text>
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#f3f5f1' },
  content: { flexGrow: 1, justifyContent: 'center', paddingHorizontal: 26, paddingVertical: 44 },
  brandMark: { width: 48, height: 48, borderRadius: 16, backgroundColor: '#286244', alignItems: 'center', justifyContent: 'center', marginBottom: 28 },
  brandMarkText: { color: '#fff', fontSize: 24, fontWeight: '800' },
  eyebrow: { color: '#46765a', fontSize: 11, fontWeight: '800', letterSpacing: 1.8 },
  title: { marginTop: 11, color: '#202a23', fontSize: 32, lineHeight: 38, fontWeight: '800', letterSpacing: -0.7 },
  description: { marginTop: 9, maxWidth: 310, color: '#667168', fontSize: 15, lineHeight: 22 },
  form: { gap: 12, marginTop: 30 },
  input: { minHeight: 54, paddingHorizontal: 16, borderWidth: 1, borderColor: '#dce2dc', borderRadius: 14, backgroundColor: '#fff', color: '#202a23', fontSize: 16 },
  primaryButton: { minHeight: 54, marginTop: 3, borderRadius: 14, backgroundColor: '#286244', alignItems: 'center', justifyContent: 'center' },
  primaryButtonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  pressed: { opacity: 0.84 },
  disabled: { opacity: 0.65 },
  switchButton: { alignItems: 'center', paddingVertical: 12 },
  switchText: { color: '#286244', fontSize: 14, fontWeight: '700' },
  error: { color: '#a23b32', fontSize: 14, lineHeight: 20 },
})
