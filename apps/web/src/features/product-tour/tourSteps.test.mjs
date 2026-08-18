import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('./tourSteps.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2023,
    verbatimModuleSyntax: false,
  },
})
const steps = await import(`data:text/javascript,${encodeURIComponent(outputText)}`)

test('week navigation target follows the visible desktop or mobile control', () => {
  assert.equal(steps.weekNavigationTargetForViewport(true), '[data-tour="week-navigation-desktop"], [data-tour="week-navigation-page"]')
  assert.equal(steps.weekNavigationTargetForViewport(false), '[data-tour="week-navigation-mobile"], [data-tour="week-navigation-page"]')
})

test('the exercise practice prompt requests the missing lateral-raise alternative', () => {
  assert.equal(steps.EXERCISE_PRACTICE_PROMPT, 'Replace Dumbbell Lateral Raise with Lean-away Cable Lateral Raise.')
})

test('guided Coach steps target the user actions in the recommendation flow', () => {
  const guidedSteps = steps.createProductTourSteps({
    hasWhoopConnection: true,
    isDesktop: true,
    actions: () => null,
  })
  const sendPromptStep = guidedSteps.find((step) => step.popover?.title === 'Use the example prompt and send it')
  const responseStep = guidedSteps.find((step) => step.popover?.title === 'Review the Coach response')
  const acceptStep = guidedSteps.find((step) => step.popover?.title === 'Accept the proposed workout')
  const createdWorkoutStep = guidedSteps.find((step) => step.popover?.title === 'Open the new workout')
  const createExerciseStep = guidedSteps.find((step) => step.popover?.title === 'Create a new exercise')
  const saveExerciseStep = guidedSteps.find((step) => step.popover?.title === 'Save the exercise')
  const replacementStep = guidedSteps.find((step) => step.popover?.title === 'Accept the replacement workout')
  const updatedWorkoutStep = guidedSteps.find((step) => step.popover?.title === 'Review the updated workout')
  const controlStep = guidedSteps.find((step) => step.popover?.title === 'You are always in control')

  assert.deepEqual(sendPromptStep?.popover?.showButtons, ['close'])
  assert.equal(sendPromptStep?.element, '[data-tour="coach-composer"]')
  assert.equal(responseStep?.element, steps.COACH_GENERATED_WORKOUT_TARGET)
  assert.equal(typeof responseStep?.onHighlightStarted, 'function')
  assert.equal(acceptStep?.element, '[data-tour="coach-accept-all"]')
  assert.equal(typeof acceptStep?.onHighlighted, 'function')
  assert.equal(createdWorkoutStep?.element, '[data-tour="created-workout"]')
  assert.equal(createdWorkoutStep?.advanceOnClick, true)
  assert.equal(createdWorkoutStep?.popover?.showButtons?.includes('next'), false)
  assert.equal(createExerciseStep?.element, '[data-tour="create-missing-exercise"]')
  assert.equal(createExerciseStep?.advanceOnClick, true)
  assert.equal(createExerciseStep?.popover?.showButtons?.includes('next'), false)
  assert.equal(saveExerciseStep?.element, '[data-tour="create-exercise-submit"]')
  assert.equal(saveExerciseStep?.popover?.showButtons?.includes('next'), false)
  assert.equal(replacementStep?.element, steps.COACH_REPLACEMENT_RECOMMENDATION_TARGET)
  assert.equal(replacementStep?.popover?.showButtons?.includes('next'), false)
  assert.equal(updatedWorkoutStep?.element, '[data-tour="workout-panel"]')
  assert.equal(typeof updatedWorkoutStep?.onHighlightStarted, 'function')
  assert.equal(controlStep?.element, '[data-tour="workout-edit"]')

  const mobileSteps = steps.createProductTourSteps({
    hasWhoopConnection: true,
    isDesktop: false,
    actions: () => null,
  })
  const mobileWeekStep = mobileSteps.find((step) => step.popover?.title === 'Your week at a glance' && step.element === '[data-tour="week-navigation-mobile"]')
  const mobileCoachStep = mobileSteps.find((step) => step.popover?.title === 'Your context-aware Coach')
  assert.deepEqual(mobileWeekStep?.popover?.showButtons, ['previous', 'close'])
  assert.equal(mobileWeekStep?.advanceOnClick, true)
  assert.deepEqual(mobileCoachStep?.popover?.showButtons, ['previous', 'close'])
  assert.equal(mobileCoachStep?.advanceOnClick, true)
  const mobileSendPromptStep = mobileSteps.find((step) => step.popover?.title === 'Use the example prompt and send it')
  const mobileAcceptStep = mobileSteps.find((step) => step.popover?.title === 'Accept the proposed workout')
  const mobileReopenCoachStep = mobileSteps.find((step) => step.popover?.title === 'Open your Coach again')
  assert.equal(mobileReopenCoachStep?.element, '[data-tour="coach-open"]')
  assert.equal(mobileReopenCoachStep?.advanceOnClick, true)
  assert.equal(mobileReopenCoachStep?.popover?.showButtons?.includes('next'), false)
  assert.equal(mobileSendPromptStep?.element, '[data-tour="coach-composer"]')
  assert.equal(mobileAcceptStep?.popover?.side, 'top')
  assert.equal(typeof mobileAcceptStep?.onHighlighted, 'function')
})
