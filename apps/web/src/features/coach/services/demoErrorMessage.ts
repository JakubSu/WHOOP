import { ApiError } from '../../../shared/api/errors'

export const DEMO_TOKEN_LIMIT_MESSAGE = 'Token limit for demo user reached. Create an account to unlock more usage.'
const DEMO_TOKEN_LIMIT_CODES = new Set(['context_limit', 'input_token_limit', 'output_token_limit', 'monthly_budget_exceeded', 'usage_limit', 'cost_limit'])

export function demoErrorMessage(reason: unknown, isDemo: boolean) {
  if (isDemo && reason instanceof ApiError && (reason.status === 429 || (typeof reason.body?.code === 'string' && DEMO_TOKEN_LIMIT_CODES.has(reason.body.code)))) {
    return DEMO_TOKEN_LIMIT_MESSAGE
  }
  return reason instanceof Error ? reason.message : 'I couldn’t complete that request.'
}

export function demoStreamErrorMessage(code: string, message: string, isDemo: boolean) {
  return isDemo && (code === 'rate_limit' || DEMO_TOKEN_LIMIT_CODES.has(code)) ? DEMO_TOKEN_LIMIT_MESSAGE : message
}
