import { create } from 'zustand'
import { type UserProfile } from '../types'

type AuthStatus = 'idle' | 'checking' | 'authenticated' | 'unauthenticated'

type AuthState = {
  accessToken: string | null
  user: UserProfile | null
  status: AuthStatus
  setChecking: () => void
  setSession: (accessToken: string, user: UserProfile) => void
  setAccessToken: (accessToken: string) => void
  setUser: (user: UserProfile) => void
  clearSession: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  status: 'idle',
  setChecking: () => set({ status: 'checking' }),
  setSession: (accessToken, user) =>
    set({ accessToken, user, status: 'authenticated' }),
  setAccessToken: (accessToken) =>
    set((state) => ({
      accessToken,
      status: state.user ? 'authenticated' : state.status,
    })),
  setUser: (user) => set({ user, status: 'authenticated' }),
  clearSession: () =>
    set({ accessToken: null, user: null, status: 'unauthenticated' }),
}))
