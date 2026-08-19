from __future__ import annotations

import boto3
from django.conf import settings


def send_whoop_access_request_email(*, user_email: str, display_name: str) -> None:
    if not settings.SES_FROM_EMAIL:
        raise RuntimeError("SES_FROM_EMAIL must be configured.")

    client = boto3.client("ses", region_name=settings.AWS_REGION)
    client.send_email(
        Source=settings.SES_FROM_EMAIL,
        Destination={"ToAddresses": [settings.WHOOP_ACCESS_REQUEST_ADMIN_EMAIL]},
        Message={
            "Subject": {"Data": "WHOOP access request"},
            "Body": {
                "Text": {
                    "Data": (
                        "A user requested access to connect WHOOP.\n\n"
                        f"Name: {display_name or '(not provided)'}\n"
                        f"Email: {user_email}\n\n"
                        "Review and approve this request in the Django admin console."
                    )
                }
            },
        },
    )
