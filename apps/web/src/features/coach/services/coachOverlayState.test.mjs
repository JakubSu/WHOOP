import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'

const source = readFileSync(new URL('./coachOverlayState.ts', import.meta.url), 'utf8')
  .replace("import { type CoachMessage, type CoachStreamEvent } from '../types'\n", '')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2023,
    verbatimModuleSyntax: false,
  },
})
const stateModule = await import(`data:text/javascript,${encodeURIComponent(outputText)}`)

const base = { messages: [], activeMessageId: null, thinking: false }
const envelope = {
  version: 1,
  sequence: 0,
  run_id: 'run-1',
  conversation_id: 'conversation-1',
  message_id: 'assistant-1',
}

test('thinking is transient and tool activity updates in place', () => {
  let state = stateModule.applyCoachStreamEvent(base, {
    event: 'message_started',
    data: envelope,
  })
  state = stateModule.applyCoachStreamEvent(state, {
    event: 'thinking_started',
    data: { ...envelope, sequence: 1, label: 'Thinking…' },
  })
  state = stateModule.applyCoachStreamEvent(state, {
    event: 'tool_started',
    data: {
      ...envelope,
      sequence: 2,
      activity: { id: 'activity-1', kind: 'recovery_data', label: 'Fetching your recovery data…', status: 'running' },
    },
  })
  state = stateModule.applyCoachStreamEvent(state, {
    event: 'tool_completed',
    data: {
      ...envelope,
      sequence: 3,
      activity: { id: 'activity-1', kind: 'recovery_data', label: 'Fetching your recovery data…', status: 'completed' },
    },
  })

  assert.equal(state.messages.length, 1)
  assert.equal(state.messages[0].activities.length, 1)
  assert.equal(state.messages[0].activities[0].status, 'completed')
  assert.equal(state.thinking, false)
})

test('completed message replaces temporary stream state and closes activity', () => {
  let state = stateModule.applyCoachStreamEvent(base, {
    event: 'message_started',
    data: envelope,
  })
  state = stateModule.applyCoachStreamEvent(state, {
    event: 'text_delta',
    data: { ...envelope, sequence: 1, delta: 'Draft text' },
  })
  state = stateModule.applyCoachStreamEvent(state, {
    event: 'completed',
    data: {
      ...envelope,
      sequence: 2,
      message: {
        id: 'assistant-1',
        role: 'assistant',
        content: 'Final text',
        created_at: '2026-08-04T18:00:00Z',
        activities: [],
        recommendation: null,
        operations: [],
      },
    },
  })

  assert.equal(state.messages[0].content, 'Final text')
  assert.equal(state.activeMessageId, null)
  assert.equal(state.thinking, false)
})

test('completed stream updates only the prior messages supplied by Coach', () => {
  const priorMessage = {
    id: 'assistant-0',
    role: 'assistant',
    content: 'Earlier recommendation',
    created_at: '2026-08-04T17:00:00Z',
    activities: [],
    recommendation: {
      id: 'recommendation-0',
      status: 'active',
      actionable: true,
      coach_card_snapshot: { version: 1, workout_groups: [] },
    },
  }
  const state = stateModule.applyCoachStreamEvent(
    {
      ...base,
      messages: [
        priorMessage,
        {
          id: 'assistant-1',
          role: 'assistant',
          content: '',
          created_at: '2026-08-04T18:00:00Z',
          activities: [],
          recommendation: null,
        },
      ],
    },
    {
      event: 'completed',
      data: {
        ...envelope,
        sequence: 1,
        message: {
          id: 'assistant-1',
          role: 'assistant',
          content: 'New recommendation',
          created_at: '2026-08-04T18:00:00Z',
          activities: [],
          recommendation: null,
        },
        recommendation_transitions: [],
        updated_messages: [{
          ...priorMessage,
          recommendation: {
            ...priorMessage.recommendation,
            status: 'superseded',
            actionable: false,
          },
        }],
      },
    },
  )

  assert.equal(state.messages[0].recommendation.status, 'superseded')
  assert.equal(state.messages[1].content, 'New recommendation')
})
