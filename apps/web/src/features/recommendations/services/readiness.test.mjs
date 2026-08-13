import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('./readiness.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2023,
    verbatimModuleSyntax: false,
  },
})
const { isRecommendationReadyToSave } = await import(
  `data:text/javascript,${encodeURIComponent(outputText)}`
)

function recommendation(status, operationStatuses) {
  return {
    id: 'rec-1',
    user_id: 'user-1',
    workout_id: 'workout-1',
    snapshot_version: 'v1',
    status,
    summary: '',
    reason: '',
    operations: operationStatuses.map((operationStatus, index) => ({
      id: `op-${index + 1}`,
      operation_type: 'update_exercise',
      status: operationStatus,
      payload: {},
      display_text: '',
    })),
    created_at: '',
    updated_at: '',
  }
}

test('workout is ready to save after every recommendation is resolved', () => {
  assert.equal(
    isRecommendationReadyToSave(
      recommendation('partial', ['accepted', 'rejected']),
    ),
    true,
  )
  assert.equal(
    isRecommendationReadyToSave(recommendation('rejected', ['rejected'])),
    true,
  )
})

test('workout is not ready to save while recommendations are still pending', () => {
  assert.equal(
    isRecommendationReadyToSave(
      recommendation('pending', ['accepted', 'pending']),
    ),
    false,
  )
})
