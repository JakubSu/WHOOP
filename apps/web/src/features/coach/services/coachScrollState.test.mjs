import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('./coachScrollState.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2023 },
})
const scrollModule = await import(`data:text/javascript,${encodeURIComponent(outputText)}`)

test('scroll following pauses when the reader moves away from the newest message', () => {
  assert.equal(scrollModule.isNearCoachScrollBottom({ scrollHeight: 900, scrollTop: 452, clientHeight: 400 }), true)
  assert.equal(scrollModule.isNearCoachScrollBottom({ scrollHeight: 900, scrollTop: 400, clientHeight: 400 }), false)
})

test('prepending older messages keeps the visible message in place', () => {
  assert.equal(scrollModule.scrollTopAfterPrepend({ previousHeight: 900, previousTop: 180, nextHeight: 1200 }), 480)
})
