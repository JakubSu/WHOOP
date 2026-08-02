import { type Recommendation } from '../recommendations/types'
import { type CoachPageContext } from './services/coachContext'

export type CoachMessageRole = 'user' | 'assistant'

export type CoachPersistedMessage = {
  id: string
  role: CoachMessageRole
  content: string
  metadata_json: Record<string, unknown>
  recommendation_id: string | null
  created_at: string
}

export type CoachConversationMessages = {
  conversation_id: string
  page_context?: CoachPageContext
  messages: CoachPersistedMessage[]
}

export type CoachChatItem =
  | {
      id: string
      type: 'message'
      role: CoachMessageRole
      content: string
    }
  | {
      id: string
      type: 'progress'
      content: string
    }
  | {
      id: string
      type: 'tool'
      content: string
    }
  | {
      id: string
      type: 'recommendation'
      recommendation: Recommendation
    }
  | {
      id: string
      type: 'error'
      content: string
    }

export type CoachStreamEvent =
  | {
      event: 'conversation_started'
      data: {
        conversation_id: string
        page_context: CoachPageContext
      }
    }
  | {
      event: 'assistant_progress'
      data: {
        message: string
      }
    }
  | {
      event: 'tool_call_started' | 'tool_call_completed'
      data: {
        label?: string
        summary?: string
        tool?: string
      }
    }
  | {
      event: 'assistant_delta'
      data: {
        text: string
      }
    }
  | {
      event: 'recommendation_created'
      data: {
        recommendation: Recommendation
      }
    }
  | {
      event: 'assistant_done'
      data: {
        message: CoachPersistedMessage
      }
    }
  | {
      event: 'error'
      data: {
        code: string
        message: string
      }
    }
