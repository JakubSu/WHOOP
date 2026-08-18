import { useProductTour } from '../../product-tour/ProductTourProvider'

export function CoachTourGuide() {
  const { guidedCoachStage } = useProductTour()
  if (!guidedCoachStage) return null
  const message = {
    initial_ready: 'Your upper-body workout request is ready. Review it, then press Send.',
    waiting_initial: 'Coach is preparing the workout. The response will appear above.',
    followup_ready: 'The follow-up is ready. Press Send to ask for the missing exercise replacement.',
    waiting_followup: 'Coach is checking the replacement exercise.',
    exercise_resolution: 'The replacement is not in your library. Use Create new exercise or Choose existing exercise in the response above.',
    waiting_resolution: 'Coach is applying your selected exercise to the recommendation.',
    complete: 'Nice work—your Coach proposal is ready to review.',
    unavailable: 'This guided example could not continue. You can keep chatting with the Coach normally.',
  }[guidedCoachStage]
  return <p className="border-t border-border bg-primary/5 px-4 py-3 text-xs font-medium text-foreground" data-tour="coach-tour-guide">{message}</p>
}
