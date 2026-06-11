import { apiRequest, setAuthHandlers } from '../../../shared/api/apiClient'
import { useAuthStore } from '../store/authStore'
import {
  type AuthSession,
  type LoginPayload,
  type RegisterPayload,
  type TokenPair,
  type UserProfile,
} from '../types'

export function configureAuthApi() {
  setAuthHandlers({
    getAccessToken: () => useAuthStore.getState().accessToken,
    refreshAccessToken: async () => {
      try {
        const session = await refreshSession()
        useAuthStore.getState().setAccessToken(session.access)
        return session.access
      } catch {
        useAuthStore.getState().clearSession()
        return null
      }
    },
    onAuthFailure: () => useAuthStore.getState().clearSession(),
  })
}

export function registerUser(payload: RegisterPayload) {
  return apiRequest<AuthSession>('/users/register/', {
    method: 'POST',
    body: JSON.stringify(payload),
    skipRefresh: true,
  })
}

export function loginUser(payload: LoginPayload) {
  return apiRequest<AuthSession>('/users/login/', {
    method: 'POST',
    body: JSON.stringify(payload),
    skipRefresh: true,
  })
}

export function refreshSession() {
  return apiRequest<TokenPair>('/users/token/refresh/', {
    method: 'POST',
    body: JSON.stringify({}),
    skipRefresh: true,
  })
}

export function getCurrentUser() {
  return apiRequest<UserProfile>('/users/me/')
}

export function logoutUser() {
  return apiRequest<void>('/users/logout/', {
    method: 'POST',
    body: JSON.stringify({}),
    skipRefresh: true,
  })
}
