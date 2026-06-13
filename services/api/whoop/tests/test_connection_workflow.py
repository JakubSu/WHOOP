from django.test import SimpleTestCase

from whoop.workflows.connection import validate_frontend_success_url


class WhoopConnectionWorkflowTests(SimpleTestCase):
    def test_accepts_allowlisted_absolute_url(self) -> None:
        url = validate_frontend_success_url(
            "http://localhost:5173/connect-whoop/success?whoop=connected",
            allowed_origins={"http://localhost:5173"},
        )

        self.assertEqual(
            url,
            "http://localhost:5173/connect-whoop/success?whoop=connected",
        )

    def test_rejects_missing_url(self) -> None:
        with self.assertRaisesMessage(ValueError, "Missing frontend success URL."):
            validate_frontend_success_url("", allowed_origins={"http://localhost:5173"})

    def test_rejects_relative_url(self) -> None:
        with self.assertRaisesMessage(
            ValueError,
            "Frontend success URL must be an absolute http or https URL.",
        ):
            validate_frontend_success_url(
                "/connect-whoop/success",
                allowed_origins={"http://localhost:5173"},
            )

    def test_rejects_disallowed_origin(self) -> None:
        with self.assertRaisesMessage(
            ValueError,
            "Frontend success URL origin is not allowed.",
        ):
            validate_frontend_success_url(
                "https://example.com/connect-whoop/success",
                allowed_origins={"http://localhost:5173"},
            )
