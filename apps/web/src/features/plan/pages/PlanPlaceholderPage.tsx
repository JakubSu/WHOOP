import { Activity } from 'lucide-react'
import { AuthShell } from '../../../shared/components/AuthShell'

export function PlanPlaceholderPage() {
  return (
    <AuthShell
      eyebrow="Training plan"
      title="Plan workspace"
      description="Your training plan will appear here in the next phase."
      icon={<Activity aria-hidden="true" />}
    >
      <div className="placeholder-panel">
        <p>
          Your plan experience is ready for implementation. WHOOP can be
          connected from onboarding when the authorization service is available.
        </p>
      </div>
    </AuthShell>
  )
}
