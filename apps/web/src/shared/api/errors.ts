type ApiErrorBody = {
  detail?: string
  [key: string]: unknown
}

export class ApiError extends Error {
  status: number
  body: ApiErrorBody | null

  constructor(message: string, status: number, body: ApiErrorBody | null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

export function getErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    if (error.body?.detail) {
      return error.body.detail
    }

    const firstFieldError = Object.values(error.body ?? {}).find(Boolean)
    if (Array.isArray(firstFieldError)) {
      return String(firstFieldError[0])
    }
    if (typeof firstFieldError === 'string') {
      return firstFieldError
    }
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Something went wrong. Please try again.'
}
