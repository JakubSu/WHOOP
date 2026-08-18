const TOUR_VERSION = 'v1'

export function productTourStorageKey(userId: string) {
  return `whoop-product-tour:${TOUR_VERSION}:${userId}`
}

export function hasCompletedProductTour(userId: string) {
  if (typeof window === 'undefined') return true
  return window.localStorage.getItem(productTourStorageKey(userId)) === 'completed'
}

export function markProductTourCompleted(userId: string) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(productTourStorageKey(userId), 'completed')
}

export function clearProductTourCompletion(userId: string) {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(productTourStorageKey(userId))
}
