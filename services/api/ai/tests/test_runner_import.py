"""Regression coverage for import-time Django app-registry safety."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


class CoachRunnerImportTests(SimpleTestCase):
    def test_runner_imports_before_django_app_setup(self) -> None:
        """ASGI may import the runner before Django populates model apps."""

        environment = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "config.settings",
        }
        result = subprocess.run(
            [sys.executable, "-c", "import ai.runner"],
            cwd=Path(__file__).resolve().parents[2],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
