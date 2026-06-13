import types
from unittest import mock

from django.test import SimpleTestCase

import config.settings as settings_module


class ProductionSettingsTests(SimpleTestCase):
    def test_load_ssm_parameters_sets_missing_secret_env_values(self):
        fake_ssm = mock.Mock()
        fake_ssm.get_parameters.return_value = {
            "Parameters": [
                {
                    "Name": "/whoop-ai-coach/prod/django/secret-key",
                    "Value": "secret-key",
                },
                {
                    "Name": "/whoop-ai-coach/prod/openai/api-key",
                    "Value": "openai-key",
                },
                {
                    "Name": "/whoop-ai-coach/prod/whoop/client-secret",
                    "Value": "whoop-secret",
                },
                {
                    "Name": "/whoop-ai-coach/prod/whoop/token-encryption-key",
                    "Value": "token-key",
                },
                {
                    "Name": "/whoop-ai-coach/prod/postgres/password",
                    "Value": "postgres-password",
                },
            ]
        }
        fake_boto3 = types.SimpleNamespace(client=mock.Mock(return_value=fake_ssm))

        with mock.patch.object(settings_module, "DEBUG", False):
            with mock.patch.dict(
                "os.environ",
                {
                    "AWS_REGION": "us-east-1",
                    "SSM_PARAMETER_PREFIX": "/whoop-ai-coach/prod",
                },
                clear=True,
            ):
                with mock.patch.dict("sys.modules", {"boto3": fake_boto3}):
                    settings_module.load_ssm_parameters()

                self.assertEqual(settings_module.os.environ["SECRET_KEY"], "secret-key")
                self.assertEqual(settings_module.os.environ["OPENAI_API_KEY"], "openai-key")
                self.assertEqual(settings_module.os.environ["WHOOP_CLIENT_SECRET"], "whoop-secret")
                self.assertEqual(settings_module.os.environ["POSTGRES_PASSWORD"], "postgres-password")

        fake_boto3.client.assert_called_once_with("ssm", region_name="us-east-1")
        fake_ssm.get_parameters.assert_called_once()
        self.assertTrue(fake_ssm.get_parameters.call_args.kwargs["WithDecryption"])
