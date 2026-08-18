export type ProductTourEligibility = {
  isAuthenticated: boolean
  hasUser: boolean
  hasCompleted: boolean
  workspaceReady: boolean
  hasAutoStarted: boolean
}

export function shouldAutoStartProductTour(eligibility: ProductTourEligibility) {
  return (
    eligibility.isAuthenticated &&
    eligibility.hasUser &&
    !eligibility.hasCompleted &&
    eligibility.workspaceReady &&
    !eligibility.hasAutoStarted
  )
}
