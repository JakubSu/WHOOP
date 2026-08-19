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

test('WHOOP prompt is suppressed during first-run onboarding and while the tour is active', () => {
  assert.equal(eligibility.shouldSuppressWhoopPrompt({ isInitialTourPending: true, isTourActive: false }), true)
  assert.equal(eligibility.shouldSuppressWhoopPrompt({ isInitialTourPending: false, isTourActive: true }), true)
  assert.equal(eligibility.shouldSuppressWhoopPrompt({ isInitialTourPending: false, isTourActive: false }), false)
})

test('week and workout pages are valid product-tour workspace routes', () => {
  assert.equal(eligibility.isProductTourWorkspaceRoute('/week'), true)
  assert.equal(eligibility.isProductTourWorkspaceRoute('/workouts/workout-1'), true)
  assert.equal(eligibility.isProductTourWorkspaceRoute('/'), false)
})
