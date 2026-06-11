import { useMutation } from '@tanstack/react-query'
import { loginUser, registerUser } from '../api/authApi'
import { useAuthStore } from '../store/authStore'
import { type RegisterPayload } from '../types'

export function useRegister() {
  const setSession = useAuthStore((state) => state.setSession)

  return useMutation({
    mutationFn: async (payload: RegisterPayload) => {
      await registerUser(payload)
      return loginUser({ email: payload.email, password: payload.password })
    },
    onSuccess: (session) => {
      setSession(session.access, session.user)
    },
  })
}
