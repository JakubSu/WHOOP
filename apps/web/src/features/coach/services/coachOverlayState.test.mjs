import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'

const coachContextSource = readFileSync(
  new URL('./coachContext.ts', import.meta.url),
  'utf8',
)
  .replace("import { matchPath } from 'react-router-dom'\n", '')
  .replace(
    "const workoutMatch = matchPath('/workouts/:workoutId', pathname)\n  const workoutId = workoutMatch?.params.workoutId",
    "const workoutId = pathname.startsWith('/workouts/') ? pathname.slice('/workouts/'.length) : undefined",
  )
const stateSource = readFileSync(
  new URL('./coachOverlayState.ts', import.meta.url),
  'utf8',
).replace(
  "import {\n  areCoachContextsEqual,\n  type CoachPageContext,\n} from './coachContext'\n",
  '',
)
const { outputText } = ts.transpileModule(`${coachContextSource}\n${stateSource}`, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2023,
    verbatimModuleSyntax: false,
  },
})
const overlayState = await import(
  `data:text/javascript,${encodeURIComponent(outputText)}`
)

test('open conversation stays visible until the next submitted turn', () => {
  const visibleContext = { page_type: 'workout', context_id: 'workout-1' }
  const currentContext = { page_type: 'training_plan', context_id: 'plan-1' }

  assert.equal(
    overlayState.shouldSwitchConversationOnSend({
      visibleContext,
      currentContext,
    }),
    true,
  )
  assert.deepEqual(
    overlayState.contextForNextSubmittedTurn({ visibleContext, currentContext }),
    currentContext,
  )
})

test('same context sends into the currently visible conversation', () => {
  const visibleContext = { page_type: 'workout', context_id: 'workout-1' }
  const currentContext = { page_type: 'workout', context_id: 'workout-1' }

  assert.equal(
    overlayState.shouldSwitchConversationOnSend({
      visibleContext,
      currentContext,
    }),
    false,
  )
  assert.deepEqual(
    overlayState.contextForNextSubmittedTurn({ visibleContext, currentContext }),
    visibleContext,
  )
})
