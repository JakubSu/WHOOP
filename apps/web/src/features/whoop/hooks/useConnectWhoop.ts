import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getWhoopAccessRequest,
  getWhoopConnectUrl,
  requestWhoopAccess,
} from '../api/whoopApi'

export function useConnectWhoop() {
  return useMutation({
    mutationFn: getWhoopConnectUrl,
  })
}

export function useWhoopAccessRequest() {
  return useQuery({
    queryKey: ['whoop-access-request'],
    queryFn: getWhoopAccessRequest,
    retry: false,
  })
}

export function useRequestWhoopAccess() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: requestWhoopAccess,
    onSuccess: (request) => {
      queryClient.setQueryData(['whoop-access-request'], request)
    },
  })
}
