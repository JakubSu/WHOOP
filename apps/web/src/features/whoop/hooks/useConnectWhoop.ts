import { useMutation } from '@tanstack/react-query'
import { getWhoopConnectUrl } from '../api/whoopApi'

export function useConnectWhoop() {
  return useMutation({
    mutationFn: getWhoopConnectUrl,
  })
}
