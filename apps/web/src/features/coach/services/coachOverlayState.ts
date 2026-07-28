import {
  areCoachContextsEqual,
  type CoachPageContext,
} from './coachContext'

export function contextForNextSubmittedTurn({
  visibleContext,
  currentContext,
}: {
  visibleContext: CoachPageContext | null
  currentContext: CoachPageContext | null
}) {
  if (!currentContext) {
    return visibleContext
  }

  return currentContext
}

export function shouldSwitchConversationOnSend({
  visibleContext,
  currentContext,
}: {
  visibleContext: CoachPageContext | null
  currentContext: CoachPageContext | null
}) {
  if (!currentContext) {
    return false
  }

  return !areCoachContextsEqual(visibleContext, currentContext)
}
