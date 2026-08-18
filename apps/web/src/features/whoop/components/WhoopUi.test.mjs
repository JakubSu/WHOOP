import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const source = (path) => readFileSync(new URL(path, import.meta.url), 'utf8')

test('WHOOP screens use responsive Tailwind layouts instead of removed legacy selectors', () => {
  const connectPage = source('../pages/ConnectWhoopPage.tsx')
  const successPage = source('../pages/ConnectWhoopSuccessPage.tsx')
  const prompt = source('../../../shared/layout/WhoopConnectionPrompt.tsx')

  for (const staleSelector of ['connect-panel', 'flow-note', 'status-card', 'spinner', 'whoop-modal', 'primary-button', 'reject-button']) {
    assert.doesNotMatch(`${connectPage}${successPage}${prompt}`, new RegExp(`className=["'][^"']*${staleSelector}`))
  }

  assert.match(connectPage, /w-full sm:w-auto/)
  assert.match(connectPage, /isRedirecting/)
  assert.match(source('../components/ConnectWhoopButton.tsx'), /Redirecting to WHOOP/)
  assert.match(successPage, /<Spinner className="size-5"/)
  assert.match(prompt, /<Dialog open/)
  assert.match(prompt, /max-h-\[calc\(100dvh-2rem\)\] overflow-y-auto/)
  assert.match(prompt, /flex-col-reverse gap-2 sm:flex-row/)
})

test('the shared button supports shadcn-style composed links', () => {
  const ui = source('../../../shared/components/ui.tsx')

  assert.match(ui, /asChild = false/)
  assert.match(ui, /SlotPrimitive\.Slot/)
})
