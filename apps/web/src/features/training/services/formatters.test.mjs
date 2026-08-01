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

test('date helpers keep explicit null fallbacks and same-day detection stable', () => {
  assert.equal(formatters.formatDate(null), 'No date')
  assert.equal(formatters.formatWeekdayDate(null), 'No date')
  assert.equal(formatters.addDaysIso('2026-06-10', -28), '2026-05-13')
  assert.equal(formatters.addDaysIso('2026-06-10', 28), '2026-07-08')
  assert.equal(formatters.isDateToday('2026-06-10', '2026-06-10'), true)
  assert.equal(formatters.isDateToday('2026-06-11', '2026-06-10'), false)
})

test('workout navigation uses date order with stable tie breakers', () => {
  const workouts = [
    workout('third', '2026-06-12', 'Push'),
    workout('second-b', '2026-06-11', 'Upper'),
    workout('first', '2026-06-10', 'Lower'),
    workout('second-a', '2026-06-11', 'Pull'),
  ]

  assert.deepEqual(formatters.getWorkoutNavigation(workouts, 'second-a'), {
    previousWorkout: workouts[2],
    nextWorkout: workouts[1],
  })
})

test('workout navigation disables missing directions at the ends', () => {
  const workouts = [
    workout('first', '2026-06-10', 'Lower'),
    workout('second', '2026-06-11', 'Upper'),
  ]

  assert.deepEqual(formatters.getWorkoutNavigation(workouts, 'first'), {
    previousWorkout: null,
    nextWorkout: workouts[1],
  })
  assert.deepEqual(formatters.getWorkoutNavigation(workouts, 'second'), {
    previousWorkout: workouts[0],
    nextWorkout: null,
  })
})

function workout(id, date, name) {
  return {
    id,
    date,
    name,
    plan: null,
    expected_time: null,
  }
}
