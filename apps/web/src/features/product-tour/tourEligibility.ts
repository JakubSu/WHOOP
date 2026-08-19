export type ProductTourEligibility = {
  isAuthenticated: boolean
  hasUser: boolean
  hasCompleted: boolean
  workspaceReady: boolean
  hasAutoStarted: boolean
}

export function isProductTourWorkspaceRoute(pathname: string) {
  return pathname === '/week' || pathname.startsWith('/workouts/')
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
