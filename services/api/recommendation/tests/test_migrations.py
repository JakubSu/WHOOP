"""Regression tests for Recommendation data migrations."""

from __future__ import annotations

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class OneActiveRecommendationPerUserMigrationTests(TransactionTestCase):
    """Ensures migration 0015 repairs existing duplicate active recommendations."""

    migrate_from = [
        ("users", "0002_user_demo_account"),
        ("recommendation", "0014_rename_presentation_snapshot"),
    ]
    migrate_to = [
        ("users", "0002_user_demo_account"),
        ("recommendation", "0015_one_active_recommendation_per_user"),
    ]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.executor = MigrationExecutor(connection)
        cls.executor.migrate(cls.migrate_from)
        cls.old_apps = cls.executor.loader.project_state(cls.migrate_from).apps

    @classmethod
    def tearDownClass(cls) -> None:
        cls.executor.migrate(cls.executor.loader.graph.leaf_nodes())
        super().tearDownClass()

    def test_keeps_newest_active_recommendation_and_stales_older_operations(
        self,
    ) -> None:
        user_model = self.old_apps.get_model("users", "User")
        recommendation_model = self.old_apps.get_model(
            "recommendation", "Recommendation"
        )
        operation_model = self.old_apps.get_model(
            "recommendation", "RecommendationOperation"
        )
        user = user_model.objects.create(email="migration-test@example.com")
        older = recommendation_model.objects.create(
            user_id=user.id,
            summary="Older recommendation",
            status="active",
        )
        newer = recommendation_model.objects.create(
            user_id=user.id,
            summary="Newer recommendation",
            status="active",
        )
        operation_model.objects.create(
            recommendation_id=older.id,
            operation_type="add_workout",
            status="pending",
            payload={},
        )

        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_to)
        apps = self.executor.loader.project_state(self.migrate_to).apps
        recommendation_model = apps.get_model("recommendation", "Recommendation")
        operation_model = apps.get_model("recommendation", "RecommendationOperation")

        older_after = recommendation_model.objects.get(pk=older.id)
        newer_after = recommendation_model.objects.get(pk=newer.id)
        operation_after = operation_model.objects.get(recommendation_id=older.id)

        self.assertEqual(older_after.status, "superseded")
        self.assertIsNotNone(older_after.superseded_at)
        self.assertEqual(newer_after.status, "active")
        self.assertEqual(operation_after.status, "stale")
        self.assertIsNotNone(operation_after.resolved_at)
