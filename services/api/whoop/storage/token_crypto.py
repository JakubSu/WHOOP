from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from cryptography.fernet import Fernet


class TokenCrypto:
    def __init__(self, key: str | None = None) -> None:
        self.key = key if key is not None else getattr(settings, "WHOOP_TOKEN_ENCRYPTION_KEY", "")
        if not self.key:
            raise ImproperlyConfigured("WHOOP_TOKEN_ENCRYPTION_KEY must be configured to store WHOOP tokens.")
        self.fernet = Fernet(self.key.encode("utf-8") if isinstance(self.key, str) else self.key)

    def encrypt(self, value: str | None) -> str:
        if not value:
            return ""
        return self.fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str | None) -> str:
        if not value:
            return ""
        return self.fernet.decrypt(value.encode("utf-8")).decode("utf-8")
