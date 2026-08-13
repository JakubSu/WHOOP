import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('./operationChanges.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2023 },
})
const operationChanges = await import(`data:text/javascript,${encodeURIComponent(outputText)}`)

test('missing update changes render as an empty list', () => {
  assert.deepEqual(operationChanges.updateChangeEntries(null), [])
  assert.deepEqual(operationChanges.updateChangeEntries(undefined), [])
})

test('update changes retain their field values', () => {
  assert.deepEqual(operationChanges.updateChangeEntries({ sets: 4, weight: '60 kg' }), [
    ['sets', 4],
    ['weight', '60 kg'],
  ])
})
