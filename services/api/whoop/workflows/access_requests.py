from __future__ import annotations

import logging

from whoop.email import send_whoop_access_request_email
from whoop.models import WhoopAccessRequest

logger = logging.getLogger(__name__)


class WhoopAccessRequestEmailError(RuntimeError):
    pass


class RequestWhoopAccessService:
    def execute(self, *, user) -> WhoopAccessRequest:
        if user.is_demo:
            raise ValueError("WHOOP access requests are unavailable in a demo session.")

        if user.whoop_connection_allowed:
            access_request = get_whoop_access_request_status(user=user)
            if access_request is None:
                return WhoopAccessRequest.objects.create(
                    user=user,
                    status=WhoopAccessRequest.Status.APPROVED,
                )
            if access_request.status != WhoopAccessRequest.Status.APPROVED:
                access_request.status = WhoopAccessRequest.Status.APPROVED
                access_request.save(update_fields=["status"])
            return access_request

        access_request, created = WhoopAccessRequest.objects.get_or_create(
            user=user,
            defaults={"status": WhoopAccessRequest.Status.PENDING},
        )

        if access_request.status == WhoopAccessRequest.Status.APPROVED:
            return access_request

        if not created and access_request.status == WhoopAccessRequest.Status.PENDING:
            return access_request

        access_request.status = WhoopAccessRequest.Status.PENDING
        access_request.reviewed_at = None
        access_request.reviewed_by = None
        access_request.admin_note = ""
        access_request.save(
            update_fields=["status", "reviewed_at", "reviewed_by", "admin_note"]
        )

        try:
            send_whoop_access_request_email(
                user_email=user.email,
                display_name=user.display_name,
            )
        except Exception as exc:
            logger.exception(
                "Failed to send WHOOP access request notification for user %s (%s).",
                user.id,
                user.email,
            )
            raise WhoopAccessRequestEmailError from exc

        return access_request


def get_whoop_access_request_status(*, user) -> WhoopAccessRequest | None:
    access_request = WhoopAccessRequest.objects.filter(user=user).first()
    if access_request is None and user.whoop_connection_allowed:
        return WhoopAccessRequest.objects.create(
            user=user,
            status=WhoopAccessRequest.Status.APPROVED,
        )
    if (
        access_request is not None
        and user.whoop_connection_allowed
        and access_request.status != WhoopAccessRequest.Status.APPROVED
    ):
        access_request.status = WhoopAccessRequest.Status.APPROVED
        access_request.save(update_fields=["status"])
    return access_request
