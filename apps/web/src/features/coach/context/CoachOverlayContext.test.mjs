import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const source = readFileSync(new URL('./CoachOverlayContext.tsx', import.meta.url), 'utf8')

test('coach page context is stable when its semantic key has not changed', () => {
  assert.match(source, /const stableContext = useMemo\(\(\) => context, \[key\]\)/)
  assert.match(source, /areCoachContextsEqual\(latest, stableContext\)/)
})
