import assert from 'node:assert/strict'
import { test } from 'node:test'
import ts from 'typescript'

const errorsSource = `
export class ApiError extends Error {
  constructor(message, status, body) { super(message); this.status = status; this.body = body }
}
`
const source = (await import('node:fs')).readFileSync(new URL('./demoErrorMessage.ts', import.meta.url), 'utf8')
  .replace("import { ApiError } from '../../../shared/api/errors'", '')
  .replace('export const DEMO_TOKEN_LIMIT_MESSAGE', 'const DEMO_TOKEN_LIMIT_MESSAGE')
  .replace('export function demoErrorMessage', 'function demoErrorMessage')
  .replace('export function demoStreamErrorMessage', 'function demoStreamErrorMessage')
  .concat('\nexport { DEMO_TOKEN_LIMIT_MESSAGE, demoErrorMessage, demoStreamErrorMessage, ApiError }')
const { outputText } = ts.transpileModule(errorsSource + source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2023 },
})
const module = await import(`data:text/javascript,${encodeURIComponent(outputText)}`)

test('demo maps an unstructured 429 limit response to the demo limit message', () => {
  const error = new module.ApiError('Request failed with status 429', 429, null)
  assert.equal(module.demoErrorMessage(error, true), module.DEMO_TOKEN_LIMIT_MESSAGE)
})

test('demo maps a streaming rate-limit event to the demo limit message', () => {
  assert.equal(
    module.demoStreamErrorMessage('rate_limit', 'The coach is busy right now.', true),
    module.DEMO_TOKEN_LIMIT_MESSAGE,
  )
})
