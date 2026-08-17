from django.contrib import admin
from django.test import SimpleTestCase

from coach.models import CoachConversation, CoachMessage, UiAction


class CoachAdminRegistrationTests(SimpleTestCase):
    def test_coach_models_are_registered_with_the_admin_site(self) -> None:
        for model in (CoachConversation, CoachMessage, UiAction):
            self.assertIn(model, admin.site._registry)
