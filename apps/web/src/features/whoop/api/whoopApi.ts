import { apiRequest } from '../../../shared/api/apiClient'
import { type WhoopSummary } from '../types'

type ConnectUrlResponse = {
  state: string
  connect_url: string
}

type GetWhoopConnectUrlOptions = {
  successUrl: string
}

export type WhoopAccessRequest = {
  status: 'none' | 'pending' | 'approved' | 'rejected'
  requested_at?: string
  reviewed_at?: string | null
}

export function getWhoopConnectUrl({ successUrl }: GetWhoopConnectUrlOptions) {
  const query = new URLSearchParams({ success_url: successUrl })
  return apiRequest<ConnectUrlResponse>(`/whoop/connect-url/?${query.toString()}`)
}

export function getWhoopSummary() {
  return apiRequest<WhoopSummary>('/whoop/summary/')
}

export function getWhoopAccessRequest() {
  return apiRequest<WhoopAccessRequest>('/whoop/access-request/')
}

export function requestWhoopAccess() {
  return apiRequest<WhoopAccessRequest>('/whoop/access-request/', {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

export function disconnectWhoop() {
  return apiRequest<void>('/whoop/disconnect/', {
    method: 'POST',
    body: JSON.stringify({}),
  })
}
