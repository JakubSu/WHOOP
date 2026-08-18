import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('./tourStorage.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2023,
    verbatimModuleSyntax: false,
  },
})
const storage = await import(`data:text/javascript,${encodeURIComponent(outputText)}`)

test('product tour completion is isolated by user and tour version', () => {
  const values = new Map()
  globalThis.window = {
    localStorage: {
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => values.set(key, value),
      removeItem: (key) => values.delete(key),
    },
  }

  assert.equal(storage.productTourStorageKey('athlete-1'), 'whoop-product-tour:v1:athlete-1')
  assert.equal(storage.hasCompletedProductTour('athlete-1'), false)
  storage.markProductTourCompleted('athlete-1')
  assert.equal(storage.hasCompletedProductTour('athlete-1'), true)
  assert.equal(storage.hasCompletedProductTour('athlete-2'), false)
  storage.clearProductTourCompletion('athlete-1')
  assert.equal(storage.hasCompletedProductTour('athlete-1'), false)
})
