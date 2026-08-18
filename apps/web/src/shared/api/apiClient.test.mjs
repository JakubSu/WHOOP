import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('./apiClient.ts', import.meta.url), 'utf8')
  .replace(/import \{ API_BASE_URL \} from '\.\.\/config\/env'\r?\n/, "const API_BASE_URL = 'http://api.test'\n")
  .replace(/import \{ ApiError \} from '\.\/errors'\r?\n/, `
class ApiError extends Error {
  constructor(message, status, body) {
    super(message)
    this.status = status
    this.body = body
  }
}
`)
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2023,
    verbatimModuleSyntax: false,
  },
})
const apiClient = await import(`data:text/javascript,${encodeURIComponent(outputText)}`)

test('apiFetch refreshes an expired token and retries an SSE request once', async () => {
  let accessToken = 'expired-token'
  let refreshes = 0
  const authorizations = []

  apiClient.setAuthHandlers({
    getAccessToken: () => accessToken,
    refreshAccessToken: async () => {
      refreshes += 1
      accessToken = 'fresh-token'
      return accessToken
    },
    onAuthFailure: () => assert.fail('refresh should succeed'),
  })

  const originalFetch = globalThis.fetch
  globalThis.fetch = async (_url, options) => {
    authorizations.push(new Headers(options.headers).get('Authorization'))
    return authorizations.length === 1
      ? new Response(null, { status: 401 })
      : new Response('event: completed\n\ndata: {}\n\n', {
          status: 200,
          headers: { 'Content-Type': 'text/event-stream' },
        })
  }

  try {
    const response = await apiClient.apiFetch('/coach/conversations/1/messages/stream', {
      method: 'POST',
      headers: { Accept: 'text/event-stream' },
      body: JSON.stringify({ content: 'Hello' }),
    })

    assert.equal(response.status, 200)
    assert.equal(refreshes, 1)
    assert.deepEqual(authorizations, ['Bearer expired-token', 'Bearer fresh-token'])
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('toApiError preserves structured streaming error codes', async () => {
  const error = await apiClient.toApiError(new Response(JSON.stringify({
    code: 'monthly_budget_exceeded',
    detail: "The AI coach's monthly allowance has been reached.",
  }), {
    status: 429,
    headers: { 'Content-Type': 'application/json' },
  }))

  assert.equal(error.status, 429)
  assert.equal(error.body.code, 'monthly_budget_exceeded')
})
