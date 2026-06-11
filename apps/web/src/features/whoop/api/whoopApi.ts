import { apiRequest } from '../../../shared/api/apiClient'

type ConnectUrlResponse = {
  state: string
  connect_url: string
}

export function getWhoopConnectUrl() {
  return apiRequest<ConnectUrlResponse>('/whoop/connect-url/')
}
