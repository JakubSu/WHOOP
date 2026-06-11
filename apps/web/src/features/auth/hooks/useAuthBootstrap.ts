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

    let isMounted = true
    setChecking()

    async function bootstrap() {
      try {
        const tokens = await refreshSession()
        useAuthStore.getState().setAccessToken(tokens.access)
        const user = await getCurrentUser()
        if (isMounted) {
          setSession(tokens.access, user)
        }
      } catch {
        if (isMounted) {
          clearSession()
        }
      }
    }

    void bootstrap()

    return () => {
      isMounted = false
    }
  }, [clearSession, setChecking, setSession, status])
}
