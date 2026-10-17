import * as SecureStore from 'expo-secure-store'
import * as Linking from 'expo-linking'
import type {
  AuthSession,
  UserProfile,
  WhoopSummary,
  Workout,
  WorkoutExercise,
  WorkoutLanding,
  WhoopAccessRequest,
} from './types'

const ACCESS_KEY = 'whoop.access'
const REFRESH_KEY = 'whoop.refresh'
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1'
const OAUTH_RETURN_URL = Linking.createURL('connect-whoop/success', { scheme: 'whoopmobile' })

let accessToken: string | null = null
let refreshToken: string | null = null
let refreshInFlight: Promise<string | null> | null = null

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function restoreTokens() {
  [accessToken, refreshToken] = await Promise.all([
    SecureStore.getItemAsync(ACCESS_KEY),
    SecureStore.getItemAsync(REFRESH_KEY),
  ])
  return Boolean(accessToken || refreshToken)
}

export async function saveSession(session: Pick<AuthSession, 'access' | 'refresh'>) {
  accessToken = session.access
  refreshToken = session.refresh ?? null
  await Promise.all([
    SecureStore.setItemAsync(ACCESS_KEY, session.access),
    session.refresh
      ? SecureStore.setItemAsync(REFRESH_KEY, session.refresh)
      : SecureStore.deleteItemAsync(REFRESH_KEY),
  ])
}

export async function clearSession() {
  accessToken = null
  refreshToken = null
  await Promise.all([
    SecureStore.deleteItemAsync(ACCESS_KEY),
    SecureStore.deleteItemAsync(REFRESH_KEY),
  ])
}

export async function apiRequest<T>(
  path: string,
  options: { method?: string; body?: unknown; authenticated?: boolean } = {},
  retried = false,
): Promise<T> {
  const authenticated = options.authenticated !== false
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (authenticated && accessToken) headers.Authorization = `Bearer ${accessToken}`

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })

  if (response.status === 401 && authenticated && !retried) {
    const nextAccess = await refreshAccessToken()
    if (nextAccess) return apiRequest<T>(path, options, true)
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const payload = await response.json()
      message = payload.detail ?? message
    } catch {
      // Keep the status-based message when the response is not JSON.
    }
    throw new ApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

async function refreshAccessToken(): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight
  if (!refreshToken) return null
  refreshInFlight = (async () => {
    try {
      const tokens = await apiRequest<{ access: string; refresh?: string }>(
        '/users/token/refresh/',
        { method: 'POST', body: { refresh: refreshToken }, authenticated: false },
        true,
      )
      await saveSession(tokens)
      return tokens.access
    } catch {
      await clearSession()
      return null
    } finally {
      refreshInFlight = null
    }
  })()
  return refreshInFlight
}

export async function login(email: string, password: string) {
  await clearSession()
  const session = await apiRequest<AuthSession>(
    '/users/login/',
    { method: 'POST', body: { email, password }, authenticated: false },
  )
  await saveSession(session)
  return session.user
}

export async function register(email: string, password: string, display_name: string) {
  await clearSession()
  const session = await apiRequest<AuthSession>(
    '/users/register/',
    { method: 'POST', body: { email, password, display_name }, authenticated: false },
  )
  await saveSession(session)
  return session.user
}

export const getCurrentUser = () => apiRequest<UserProfile>('/users/me/')
export const getWhoopSummary = () => apiRequest<WhoopSummary>('/whoop/summary/')
export const getWhoopAccessRequest = () => apiRequest<WhoopAccessRequest>('/whoop/access-request/')
export const requestWhoopAccess = () =>
  apiRequest<WhoopAccessRequest>('/whoop/access-request/', { method: 'POST', body: {} })

export async function getWhoopConnectUrl() {
  const query = new URLSearchParams({ success_url: OAUTH_RETURN_URL })
  return apiRequest<{ connect_url: string }>(`/whoop/connect-url/?${query.toString()}`)
}

export const getWorkoutLanding = (today: string) =>
  apiRequest<WorkoutLanding>(`/workouts/landing/?today=${today}`)
export const getWorkout = (id: string) => apiRequest<Workout>(`/workouts/${id}/`)
export const getWorkoutExercises = (id: string) =>
  apiRequest<WorkoutExercise[]>(`/workouts/${id}/exercises/`)

export async function logout() {
  try {
    if (refreshToken) {
      await apiRequest('/users/logout/', {
        method: 'POST',
        body: { refresh: refreshToken },
        authenticated: false,
      })
    }
  } finally {
    await clearSession()
  }
}

export const whoopOauthReturnUrl = OAUTH_RETURN_URL
