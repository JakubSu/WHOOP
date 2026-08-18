import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('./tourEligibility.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2023,
    verbatimModuleSyntax: false,
  },
})
const eligibility = await import(`data:text/javascript,${encodeURIComponent(outputText)}`)

const readyFirstSession = {
  isAuthenticated: true,
  hasUser: true,
  hasCompleted: false,
  workspaceReady: true,
  hasAutoStarted: false,
}

test('product tour starts only for a ready first authenticated session', () => {
  assert.equal(eligibility.shouldAutoStartProductTour(readyFirstSession), true)
  assert.equal(eligibility.shouldAutoStartProductTour({ ...readyFirstSession, hasCompleted: true }), false)
  assert.equal(eligibility.shouldAutoStartProductTour({ ...readyFirstSession, workspaceReady: false }), false)
  assert.equal(eligibility.shouldAutoStartProductTour({ ...readyFirstSession, isAuthenticated: false }), false)
  assert.equal(eligibility.shouldAutoStartProductTour({ ...readyFirstSession, hasAutoStarted: true }), false)
})
