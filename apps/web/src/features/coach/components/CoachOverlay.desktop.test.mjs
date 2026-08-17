import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const source = readFileSync(new URL('./CoachOverlay.tsx', import.meta.url), 'utf8')

test('desktop startup loads the latest conversation for the initially open panel', () => {
  assert.match(
    source,
    /useEffect\(\(\) => \{[\s\S]*!isDesktop[\s\S]*desktop\.mode === 'collapsed'[\s\S]*chat\.loadLatestConversation\(\)/,
  )
})
