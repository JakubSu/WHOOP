import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('./formatters.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2023,
    verbatimModuleSyntax: false,
  },
})
const formatters = await import(
  `data:text/javascript,${encodeURIComponent(outputText)}`
)

test('planned workout title prefers Today when the workout is scheduled for today', () => {
  assert.equal(formatters.getWorkoutScreenTitle('2026-06-10', true), 'Today')
})

test('landing eyebrow shows the no-workout-today message when present', () => {
  assert.equal(
    formatters.getWorkoutScreenEyebrow('No workout scheduled today'),
    'No workout scheduled today',
  )
  assert.equal(formatters.getWorkoutScreenEyebrow(null), 'Workout')
})

test('date helpers keep explicit null fallbacks and same-day detection stable', () => {
  assert.equal(formatters.formatDate(null), 'No date')
  assert.equal(formatters.formatWeekdayDate(null), 'No date')
  assert.equal(formatters.isDateToday('2026-06-10', '2026-06-10'), true)
  assert.equal(formatters.isDateToday('2026-06-11', '2026-06-10'), false)
})
