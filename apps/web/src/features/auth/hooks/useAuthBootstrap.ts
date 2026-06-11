import { useEffect } from 'react'
import { configureAuthApi, getCurrentUser, refreshSession } from '../api/authApi'
import { useAuthStore } from '../store/authStore'

export function useAuthBootstrap() {
  const status = useAuthStore((state) => state.status)
  const setChecking = useAuthStore((state) => state.setChecking)
  const setSession = useAuthStore((state) => state.setSession)
  const clearSession = useAuthStore((state) => state.clearSession)

  useEffect(() => {
    configureAuthApi()
  }, [])

  useEffect(() => {
    if (status !== 'idle') {
      return
    }

    setChecking()

    async function bootstrap() {
      try {
        const tokens = await refreshSession()
        useAuthStore.getState().setAccessToken(tokens.access)
        const user = await getCurrentUser()
        setSession(tokens.access, user)
      } catch {
        clearSession()
      }
    }

    void bootstrap()
  }, [clearSession, setChecking, setSession, status])
}
