import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'

function stripReactRouterImport(source) {
  return source
    .replace("import { matchPath } from 'react-router-dom'\n", '')
    .replace(
      "const workoutMatch = matchPath('/workouts/:workoutId', pathname)\n  const workoutId = workoutMatch?.params.workoutId",
      "const workoutId = pathname.startsWith('/workouts/') ? pathname.slice('/workouts/'.length) : undefined",
    )
}

const source = stripReactRouterImport(
  readFileSync(new URL('./coachContext.ts', import.meta.url), 'utf8'),
)
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2023,
    verbatimModuleSyntax: false,
  },
})
const coachContext = await import(
  `data:text/javascript,${encodeURIComponent(outputText)}`
)

test('coach context is only produced for coach-capable routes', () => {
  assert.deepEqual(coachContext.getCoachPageContextForRoute('/training'), {
    page_type: 'today_workout',
    context_id: '',
  })
  assert.deepEqual(coachContext.getCoachPageContextForRoute('/workouts/w-1'), {
    page_type: 'workout',
    context_id: 'w-1',
  })
  assert.equal(coachContext.getCoachPageContextForRoute('/week'), null)
  assert.equal(coachContext.getCoachPageContextForRoute('/login'), null)
  assert.equal(coachContext.getCoachPageContextForRoute('/connect-whoop'), null)
})

test('coach launcher labels the current context compactly', () => {
  assert.equal(
    coachContext.labelForCoachContext({
      page_type: 'today_workout',
      context_id: '',
    }),
    'Today',
  )
  assert.equal(coachContext.labelForCoachContext(null), 'Coach')
})
