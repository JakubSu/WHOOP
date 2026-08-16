import { API_BASE_URL } from '../config/env'
import { ApiError } from './errors'

type ApiRequestOptions = RequestInit & {
  skipRefresh?: boolean
  baseUrl?: string
}

type AuthHandlers = {
  getAccessToken: () => string | null
  refreshAccessToken: () => Promise<string | null>
  onAuthFailure: () => void
}

let authHandlers: AuthHandlers | null = null
let refreshPromise: Promise<string | null> | null = null

export function setAuthHandlers(handlers: AuthHandlers) {
  authHandlers = handlers
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const response = await apiFetch(path, options)

  if (!response.ok) {
    throw await toApiError(response)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export async function apiFetch(
  path: string,
  options: ApiRequestOptions = {},
): Promise<Response> {
  return fetchWithAuth(path, options, false)
}

async function fetchWithAuth(
  path: string,
  options: ApiRequestOptions,
  hasRetried: boolean,
): Promise<Response> {
  const { baseUrl = API_BASE_URL, ...fetchOptions } = options
  const response = await fetch(`${baseUrl}${path}`, {
    ...fetchOptions,
    credentials: 'include',
    headers: buildHeaders(options),
  })

  if (response.status === 401 && !options.skipRefresh && !hasRetried) {
    const nextAccessToken = await refreshAccessToken()

    if (nextAccessToken) {
      return fetchWithAuth(path, options, true)
    }

    authHandlers?.onAuthFailure()
  }

  return response
}

function buildHeaders(options: ApiRequestOptions) {
  const headers = new Headers(options.headers)
  const token = authHandlers?.getAccessToken()

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  return headers
}

async function refreshAccessToken() {
  if (!authHandlers) {
    return null
  }

  refreshPromise ??= authHandlers.refreshAccessToken().finally(() => {
    refreshPromise = null
  })

  return refreshPromise
}

async function toApiError(response: Response) {
  let body = null

  try {
    body = await response.json()
  } catch {
    body = null
  }

  const message =
    body?.detail ?? `Request failed with status ${response.status}`

  return new ApiError(message, response.status, body)
}
