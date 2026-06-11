import { useMutation } from '@tanstack/react-query'
import { loginUser } from '../api/authApi'
import { useAuthStore } from '../store/authStore'
import { type LoginPayload } from '../types'

export function useLogin() {
  const setSession = useAuthStore((state) => state.setSession)

  return useMutation({
    mutationFn: (payload: LoginPayload) => loginUser(payload),
    onSuccess: (session) => {
      setSession(session.access, session.user)
    },
  })
}
