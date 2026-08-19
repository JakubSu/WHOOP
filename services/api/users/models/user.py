import uuid
from typing import TYPE_CHECKING, ClassVar

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone

if TYPE_CHECKING:
    from whoop.models import WhoopAccessRequest


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    def create_user(
        self, email: str, password: str | None = None, **extra_fields: object
    ) -> "User":
        if not email:
            raise ValueError("Email is required.")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: object
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    if TYPE_CHECKING:
        whoop_access_request: WhoopAccessRequest

    class AccountType(models.TextChoices):
        NORMAL = "normal", "Normal"
        DEMO = "demo", "Demo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=200, blank=True, default="")
    whoop_user_id = models.CharField(max_length=64, blank=True, default="")
    account_type = models.CharField(
        max_length=16, choices=AccountType.choices, default=AccountType.NORMAL
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        ordering = ["email"]

    def __str__(self) -> str:
        return self.email

    @property
    def is_demo(self) -> bool:
        return self.account_type == self.AccountType.DEMO

    @property
    def whoop_connection_allowed(self) -> bool:
        if self.is_demo:
            return False
        if self.email.casefold() in {
            email.casefold() for email in settings.WHOOP_ACCESS_ALLOWLIST
        }:
            return True
        try:
            return self.whoop_access_request.status == "approved"
        except ObjectDoesNotExist:
            return False

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= timezone.now()
