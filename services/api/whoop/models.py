import uuid

from django.conf import settings
from django.db import models


class WhoopConnection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=64, unique=True)
    whoop_user_id = models.CharField(max_length=64)
    access_token_encrypted = models.TextField()
    refresh_token_encrypted = models.TextField(blank=True, default="")
    expires_at = models.DateTimeField(null=True, blank=True)
    scopes = models.TextField(blank=True, default="")
    connected_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-connected_at"]

    def __str__(self) -> str:
        return f"WHOOP connection for {self.user_id}"


class WhoopOAuthState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.CharField(max_length=255, unique=True)
    user_id = models.CharField(max_length=64)
    frontend_success_url = models.URLField(max_length=2048, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["state"], name="whoop_oauth_state_idx"),
            models.Index(
                fields=["user_id", "created_at"],
                name="whoop_oauth_user_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"WHOOP OAuth state for {self.user_id}"


class WhoopAccessRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="whoop_access_request",
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_whoop_access_requests",
    )
    admin_note = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["status", "-requested_at"]

    def __str__(self) -> str:
        return f"WHOOP access request for {self.user.email} ({self.status})"


class WhoopSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=64)
    snapshot_date = models.DateField()
    recovery_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    sleep_performance_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    day_strain = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    hrv_rmssd_milli = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    resting_heart_rate = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    sleep_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    recent_workout_count = models.PositiveIntegerField(default=0)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-snapshot_date", "-created_at"]
        indexes = [
            models.Index(
                fields=["user_id", "snapshot_date"],
                name="whoop_snapshot_user_date_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"WHOOP snapshot for {self.user_id} on {self.snapshot_date}"
