from django.core.management.base import BaseCommand

from training.services.shared_exercise_bank import sync_shared_exercise_bank


class Command(BaseCommand):
    help = "Create or update shared exercises from training/data/shared_exercise_bank.json."

    def handle(self, *args: object, **options: object) -> None:
        result = sync_shared_exercise_bank()
        self.stdout.write(
            self.style.SUCCESS(
                "Shared exercise bank synchronized: "
                f"{result.created} created, {result.updated} updated, "
                f"{result.unchanged} unchanged."
            )
        )
