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

test('the exercise practice prompt is a fixed prefill request', () => {
  assert.equal(steps.EXERCISE_PRACTICE_PROMPT, 'Replace barbell rows with chest-supported dumbbell rows.')
})
