from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from coach.models import CoachConversation
from recommendation.models import Recommendation
from training.models import Exercise, TrainingPlan, Workout
from users.models import User
from whoop.models import WhoopConnection, WhoopOAuthState, WhoopSnapshot


class Command(BaseCommand):
    help = "Delete expired demo accounts and their non-relational workspace data."

    def handle(self, *args, **options):
        expired_users = User.objects.filter(
            account_type=User.AccountType.DEMO, expires_at__lte=timezone.now()
        )
        user_ids = [str(user_id) for user_id in expired_users.values_list("id", flat=True)]
        if not user_ids:
            self.stdout.write("No expired demo users found.")
            return

        with transaction.atomic():
            # Delete recommendations before their nullable conversation/message links
            # can be cleared by the coach conversation cascade.
            Recommendation.objects.filter(user_id__in=user_ids).delete()
            # Deleting conversations cascades to their messages and UI actions.
            CoachConversation.objects.filter(user_id__in=user_ids).delete()
            Workout.objects.filter(user_id__in=user_ids).delete()
            TrainingPlan.objects.filter(user_id__in=user_ids).delete()
            Exercise.objects.filter(user_id__in=user_ids).delete()
            WhoopSnapshot.objects.filter(user_id__in=user_ids).delete()
            WhoopConnection.objects.filter(user_id__in=user_ids).delete()
            WhoopOAuthState.objects.filter(user_id__in=user_ids).delete()
            deleted_count, _ = expired_users.delete()
        self.stdout.write(self.style.SUCCESS(f"Removed {len(user_ids)} expired demo users ({deleted_count} records)."))
