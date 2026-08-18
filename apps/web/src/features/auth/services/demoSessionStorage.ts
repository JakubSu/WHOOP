import { type UserProfile } from '../types'

const DEMO_SESSION_KEY = 'whoop-demo-session'

type StoredDemoSession = {
  access: string
  user: UserProfile
}

export function saveDemoSession(session: StoredDemoSession) {
  window.sessionStorage.setItem(DEMO_SESSION_KEY, JSON.stringify(session))
}

export function loadDemoSession(): StoredDemoSession | null {
  const raw = window.sessionStorage.getItem(DEMO_SESSION_KEY)
  if (!raw) return null
  try {
    const session = JSON.parse(raw) as StoredDemoSession
    return session.access && session.user?.account_type === 'demo' ? session : null
  } catch {
    clearDemoSession()
    return null
  }
}

export function clearDemoSession() {
  window.sessionStorage.removeItem(DEMO_SESSION_KEY)
}
