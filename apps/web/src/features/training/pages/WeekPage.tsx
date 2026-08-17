import { useSearchParams } from 'react-router-dom'
import { TrainingLayout } from '../../../shared/layout/TrainingLayout'
import { useCoachPageContext } from '../../coach/context/CoachOverlayContext'
import { WeekPlanList } from '../components/WeekPlanList'

export function WeekPage() {
  const [searchParams] = useSearchParams()
  useCoachPageContext(null)

  return <TrainingLayout showWeekNavigator={false}><section className="mx-auto min-h-0 w-full max-w-2xl overflow-y-auto px-4 py-6 sm:px-6 lg:max-w-none lg:px-8 lg:py-7"><WeekPlanList date={searchParams.get('date')} /></section></TrainingLayout>
}
