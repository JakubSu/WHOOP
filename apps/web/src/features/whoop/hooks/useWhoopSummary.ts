import { useQuery } from '@tanstack/react-query'
import { ApiError } from '../../../shared/api/errors'
import { getWhoopSummary } from '../api/whoopApi'
import { useAuthStore } from '../../auth/store/authStore'

const disconnectedSummary = {
  connected: false,
  recovery_score: null,
  sleep_performance_percent: null,
  day_strain: null,
}

export function useWhoopSummary() {
  const userId = useAuthStore((state) => state.user?.id)

  return useQuery({
    queryKey: ['whoop-summary', userId],
    queryFn: async () => {
      try {
        return await getWhoopSummary()
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return disconnectedSummary
        }
        throw error
      }
    },
    enabled: Boolean(userId),
  })
}
